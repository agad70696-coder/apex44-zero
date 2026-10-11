"""Fail-closed evaluator for fourteen APEX44 scientific-control contracts.

Thresholds are proposed operational values pending preregistration review. PASS_SCOPED
validates bounded controls only; it does not establish a claim or authorize release.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
DEFAULT_CONTRACT = HERE / "scientific_control_contract.json"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")

def number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)

def text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())

def subject_error(document: dict[str, Any]) -> str | None:
    subject = document.get("subject")
    if not isinstance(subject, dict):
        return "SUBJECT_PROVENANCE_MISSING"
    if not isinstance(subject.get("commit_sha"), str) or not COMMIT.fullmatch(subject["commit_sha"]):
        return "SUBJECT_COMMIT_SHA_INVALID"
    if not isinstance(subject.get("dataset_sha256"), str) or not SHA256.fullmatch(subject["dataset_sha256"]):
        return "SUBJECT_DATASET_SHA256_INVALID"
    if not text(subject.get("model_id")):
        return "SUBJECT_MODEL_ID_MISSING"
    return None

def evidence_error(observation: dict[str, Any], evidence_root: Path) -> str | None:
    evidence = observation.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        return "EVIDENCE_MISSING"
    root = evidence_root.resolve()
    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            return f"EVIDENCE_ITEM_{index}_INVALID"
        if not text(item.get("source")) or not text(item.get("role")):
            return f"EVIDENCE_ITEM_{index}_SOURCE_OR_ROLE_MISSING"
        digest = item.get("sha256")
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            return f"EVIDENCE_ITEM_{index}_SHA256_INVALID"
        raw_path = item.get("path")
        if not text(raw_path):
            return f"EVIDENCE_ITEM_{index}_PATH_MISSING"
        relative = PurePosixPath(raw_path)
        if relative.is_absolute() or any(part in ("", ".", "..") for part in relative.parts):
            return f"EVIDENCE_ITEM_{index}_PATH_INVALID"
        candidate = root.joinpath(*relative.parts)
        try:
            resolved = candidate.resolve(strict=True)
        except (OSError, RuntimeError):
            return f"EVIDENCE_ITEM_{index}_FILE_MISSING"
        try:
            resolved.relative_to(root)
        except ValueError:
            return f"EVIDENCE_ITEM_{index}_PATH_OUTSIDE_ROOT"
        if not resolved.is_file():
            return f"EVIDENCE_ITEM_{index}_NOT_A_FILE"
        try:
            actual = hashlib.sha256(resolved.read_bytes()).hexdigest()
        except OSError:
            return f"EVIDENCE_ITEM_{index}_FILE_UNREADABLE"
        if actual != digest:
            return f"EVIDENCE_ITEM_{index}_SHA256_MISMATCH"
    return None

def kendall_tau(first: dict[str, float], second: dict[str, float]) -> float:
    keys = sorted(set(first) & set(second))
    concordance = pairs = 0
    for index, left in enumerate(keys):
        for right in keys[index + 1:]:
            pairs += 1
            product = (first[left] - first[right]) * (second[left] - second[right])
            concordance += 1 if product > 0 else -1 if product < 0 else 0
    return concordance / pairs if pairs else 0.0

def assess(control: dict[str, Any], metrics: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    cid, limits = control["id"], control["acceptance"]
    if cid in ("S1", "S2"):
        density, choices = metrics["constraint_density"], metrics["choice_cardinality"]
        if not number(density) or not 0 <= density <= 1 or not isinstance(choices, int) or isinstance(choices, bool) or choices < 1:
            return "BLOCKED", "METRIC_TYPE_OR_RANGE_INVALID", {}
        accepted = (density <= limits["constraint_density_max"] and choices >= limits["choice_cardinality_min"]) if cid == "S1" else (density >= limits["constraint_density_min"] and choices <= limits["choice_cardinality_max"])
        return ("PASS" if accepted else "FAIL", "ACCEPTANCE_MET" if accepted else "ACCEPTANCE_NOT_MET", {"constraint_density": density, "choice_cardinality": choices})
    if cid == "S3":
        probabilities, observed = metrics["probabilities"], metrics["surprisal_bits"]
        if not isinstance(probabilities, list) or not isinstance(observed, list) or len(probabilities) != len(observed) or len(probabilities) < limits["minimum_points"]:
            return "BLOCKED", "PROBABILITY_SERIES_INCOMPLETE", {}
        if any(not number(p) or p <= 0 or p > 1 for p in probabilities) or any(not number(s) for s in observed):
            return "BLOCKED", "PROBABILITY_OR_SURPRISAL_INVALID", {}
        maximum_error = max(abs(value + math.log2(probability)) for probability, value in zip(probabilities, observed))
        ordered = sorted(zip(probabilities, observed))
        monotonic = all(ordered[i][1] > ordered[i + 1][1] for i in range(len(ordered) - 1))
        accepted = maximum_error <= limits["absolute_tolerance"] and monotonic
        return ("PASS" if accepted else "FAIL", "CALIBRATION_MET" if accepted else "CALIBRATION_MISMATCH", {"max_absolute_error_bits": maximum_error, "strict_inverse_order": monotonic})
    if cid == "S4":
        pairs = metrics["matched_score_pairs"]
        if not isinstance(pairs, list) or len(pairs) < limits["minimum_pairs"]:
            return "BLOCKED", "MATCHED_PAIRS_INCOMPLETE", {}
        deltas = []
        for pair in pairs:
            if not isinstance(pair, dict) or not number(pair.get("short_score")) or not number(pair.get("padded_score")):
                return "BLOCKED", "MATCHED_PAIR_INVALID", {}
            deltas.append(abs(pair["short_score"] - pair["padded_score"]))
        maximum = max(deltas)
        accepted = maximum <= limits["maximum_absolute_score_delta"]
        return ("PASS" if accepted else "FAIL", "LENGTH_INVARIANCE_MET" if accepted else "LENGTH_CONFOUNDING_DETECTED", {"max_absolute_delta": maximum, "pair_count": len(pairs)})
    if cid == "S5":
        baseline, curve = metrics["baseline_score"], metrics["perturbation_curve"]
        if not number(baseline) or not isinstance(curve, list):
            return "BLOCKED", "PERTURBATION_CURVE_INVALID", {}
        by_level = {}
        for point in curve:
            if not isinstance(point, dict) or not isinstance(point.get("noise_percent"), int) or not number(point.get("score")):
                return "BLOCKED", "PERTURBATION_POINT_INVALID", {}
            level = point["noise_percent"]
            if level in by_level:
                return "BLOCKED", "DUPLICATE_NOISE_LEVEL", {}
            by_level[level] = point["score"]
        if not set(limits["required_noise_percent_levels"]).issubset(by_level):
            return "BLOCKED", "REQUIRED_NOISE_LEVEL_MISSING", {"levels": sorted(by_level)}
        if abs(by_level[0] - baseline) > limits["absolute_tolerance"]:
            return "FAIL", "ZERO_NOISE_BASELINE_MISMATCH", {}
        maximum = max(abs(value - baseline) for value in by_level.values())
        accepted = maximum <= limits["maximum_absolute_score_delta"]
        return ("PASS" if accepted else "FAIL", "SENSITIVITY_WITHIN_BUDGET" if accepted else "SENSITIVITY_BUDGET_EXCEEDED", {"max_absolute_delta": maximum, "levels": sorted(by_level)})
    if cid == "S6":
        by_representation, required = metrics["scores_by_representation"], limits["required_representations"]
        if not isinstance(by_representation, dict) or any(rep not in by_representation for rep in required):
            return "BLOCKED", "REPRESENTATION_MISSING", {}
        for representation in required:
            scores = by_representation[representation]
            if not isinstance(scores, dict) or len(scores) < limits["minimum_candidates"] or any(not text(key) or not number(value) for key, value in scores.items()):
                return "BLOCKED", f"REPRESENTATION_{representation}_SCORES_INVALID", {}
        shared = set.intersection(*(set(by_representation[rep]) for rep in required))
        if len(shared) < limits["minimum_candidates"]:
            return "BLOCKED", "SHARED_CANDIDATE_SET_TOO_SMALL", {}
        taus = {f"{left}:{right}": kendall_tau({k: by_representation[left][k] for k in shared}, {k: by_representation[right][k] for k in shared}) for i, left in enumerate(required) for right in required[i + 1:]}
        minimum = min(taus.values())
        accepted = minimum >= limits["minimum_pairwise_kendall_tau"]
        return ("PASS" if accepted else "FAIL", "RANK_STABILITY_MET" if accepted else "REPRESENTATION_RANK_SHIFT", {"pairwise_kendall_tau": taus, "minimum_pairwise_kendall_tau": minimum})
    if cid == "S9":
        fixture_id, seed, detected, false_positive_rate = (metrics[key] for key in ("artifact_fixture_id", "generator_seed", "injected_artifact_detected", "clean_control_false_positive_rate"))
        if not text(fixture_id) or not text(str(seed)) or not isinstance(detected, bool) or not number(false_positive_rate) or not 0 <= false_positive_rate <= 1:
            return "BLOCKED", "GENERATOR_BIAS_METRIC_INVALID", {}
        accepted = detected and false_positive_rate <= limits["clean_control_false_positive_rate_max"]
        return ("PASS" if accepted else "FAIL", "ARTIFACT_CONTROL_MET" if accepted else "GENERATOR_BIAS_CONTROL_FAILED", {"artifact_fixture_id": fixture_id, "generator_seed": seed, "clean_control_false_positive_rate": false_positive_rate})
    if cid == "S10":
        keys = ("leakage_injected_detected", "promotion_allowed_on_leaked_fixture", "clean_fixture_not_flagged")
        if any(not isinstance(metrics.get(key), bool) for key in keys):
            return "BLOCKED", "LEAKAGE_METRIC_INVALID", {}
        accepted = metrics[keys[0]] and not metrics[keys[1]] and metrics[keys[2]]
        return ("PASS" if accepted else "FAIL", "LEAKAGE_SENTINEL_ENFORCED" if accepted else "LEAKAGE_SENTINEL_FAILED", {key: metrics[key] for key in keys})
    if cid == "S11":
        legal, illegal = metrics["legal_transform_results"], metrics["illegal_transform_results"]
        if not isinstance(legal, list) or not isinstance(illegal, list) or len(legal) < limits["minimum_legal_cases"] or len(illegal) < limits["minimum_illegal_cases"]:
            return "BLOCKED", "TRANSFORM_CASES_INCOMPLETE", {}
        if any(not isinstance(item, dict) or not text(item.get("transform_id")) or not isinstance(item.get("scope_preserved"), bool) for item in legal):
            return "BLOCKED", "LEGAL_TRANSFORM_CASE_INVALID", {}
        if any(not isinstance(item, dict) or not text(item.get("transform_id")) or not isinstance(item.get("rejected"), bool) for item in illegal):
            return "BLOCKED", "ILLEGAL_TRANSFORM_CASE_INVALID", {}
        accepted = all(item["scope_preserved"] for item in legal) and all(item["rejected"] for item in illegal)
        return ("PASS" if accepted else "FAIL", "TRANSFORM_POLICY_ENFORCED" if accepted else "TRANSFORM_POLICY_VIOLATION", {"legal_cases": len(legal), "illegal_cases": len(illegal)})
    if cid == "S12":
        candidate, baseline, adjusted_p = (metrics[key] for key in ("candidate_score", "strongest_baseline_score", "adjusted_p_value"))
        if any(not number(value) for value in (candidate, baseline, adjusted_p)) or not 0 <= adjusted_p <= 1:
            return "BLOCKED", "TOURNAMENT_METRIC_INVALID", {}
        advantage = candidate - baseline
        accepted = advantage >= limits["minimum_advantage"] and adjusted_p <= limits["maximum_adjusted_p_value"]
        return ("PASS" if accepted else "FAIL", "ALTERNATIVE_ADVANTAGE_ESTABLISHED" if accepted else "ALTERNATIVE_ADVANTAGE_NOT_ESTABLISHED", {"advantage": advantage, "adjusted_p_value": adjusted_p})
    if cid == "S13":
        hidden, promoted = metrics["hidden_constraints"], metrics["unverified_promoted_as_fact"]
        if not isinstance(hidden, list) or not isinstance(promoted, bool):
            return "BLOCKED", "HIDDEN_CONSTRAINT_METRIC_INVALID", {}
        if any(not isinstance(item, dict) or item.get("status") != "CANDIDATE" or not text(item.get("provenance_ref")) for item in hidden):
            return "FAIL", "HIDDEN_CONSTRAINT_PROVENANCE_OR_STATUS_VIOLATION", {}
        accepted = len(hidden) >= limits["minimum_candidates"] and not promoted
        return ("PASS" if accepted else "FAIL", "HYPOTHESIS_BOUNDARY_PRESERVED" if accepted else "HIDDEN_CONSTRAINT_BOUNDARY_FAILED", {"candidate_count": len(hidden), "unverified_promoted_as_fact": promoted})
    if cid == "S14":
        variants, promoted = metrics["annotation_variant_scores"], metrics["claim_promoted"]
        if not isinstance(variants, dict) or not isinstance(promoted, bool) or any(not text(key) or not number(value) for key, value in variants.items()):
            return "BLOCKED", "MULTIVERSE_METRIC_INVALID", {}
        if len(variants) < limits["minimum_variants"]:
            return "BLOCKED", "ANNOTATION_VARIANTS_INCOMPLETE", {}
        spread = max(variants.values()) - min(variants.values())
        accepted = spread <= limits["maximum_claim_score_spread"] or not promoted
        return ("PASS" if accepted else "FAIL", "MULTIVERSE_DISAGREEMENT_HANDLED" if accepted else "CLAIM_PROMOTED_DESPITE_DISAGREEMENT", {"variant_count": len(variants), "score_spread": spread, "claim_promoted": promoted})
    if cid == "S15":
        keys = ("critical_failure_injected", "promotion_blocked", "override_authority_checked")
        if any(not isinstance(metrics.get(key), bool) for key in keys):
            return "BLOCKED", "KILL_SWITCH_METRIC_INVALID", {}
        accepted = all(metrics[key] for key in keys)
        return ("PASS" if accepted else "FAIL", "KILL_SWITCH_ENFORCED" if accepted else "KILL_SWITCH_BYPASS_OR_FAILURE", {key: metrics[key] for key in keys})
    if cid == "S16":
        keys = ("failure_detected", "failure_type", "location", "evidence_ref", "reproduction_command")
        if not isinstance(metrics.get("failure_detected"), bool) or any(not text(metrics.get(key)) for key in keys[1:]):
            return "BLOCKED", "FAILURE_PROFILE_INCOMPLETE", {}
        accepted = metrics["failure_detected"] and metrics["failure_type"] in limits["allowed_failure_types"]
        return ("PASS" if accepted else "FAIL", "FAILURE_TYPED_AND_LOCALIZED" if accepted else "FAILURE_PROFILE_UNUSABLE", {key: metrics[key] for key in keys})
    return "BLOCKED", "NO_EVALUATOR_FOR_CONTROL", {}

def evaluate(document: dict[str, Any], contract: dict[str, Any], evidence_root: Path | None = None) -> dict[str, Any]:
    document = document if isinstance(document, dict) else {}
    evidence_root = evidence_root or REPO_ROOT
    controls, raw = contract.get("controls", []), document.get("observations", [])
    observations, duplicates = {}, set()
    if isinstance(raw, list):
        for observation in raw:
            if isinstance(observation, dict) and text(observation.get("control_id")):
                cid = observation["control_id"]
                if cid in observations:
                    duplicates.add(cid)
                observations[cid] = observation
    subject_issue = subject_error(document)
    rows = []
    for control in controls:
        cid = control["id"]
        observation = observations.get(cid)
        metrics = observation.get("metrics") if isinstance(observation, dict) else None
        if cid in duplicates:
            status, reason, details = "BLOCKED", "DUPLICATE_CONTROL_OBSERVATION", {}
        elif observation is None:
            status, reason, details = "BLOCKED", "OBSERVATION_MISSING", {}
        elif subject_issue:
            status, reason, details = "BLOCKED", subject_issue, {}
        elif (issue := evidence_error(observation, evidence_root)):
            status, reason, details = "BLOCKED", issue, {}
        elif not isinstance(metrics, dict):
            status, reason, details = "BLOCKED", "METRICS_MISSING", {}
        elif (missing := [key for key in control.get("metrics_required", []) if key not in metrics]):
            status, reason, details = "BLOCKED", "REQUIRED_METRICS_MISSING", {"missing": missing}
        else:
            try:
                status, reason, details = assess(control, metrics)
            except (KeyError, TypeError, ValueError, OverflowError):
                status, reason, details = "BLOCKED", "METRICS_SCHEMA_INVALID", {}
        rows.append({"control_id": cid, "name": control["name"], "status": status, "reason": reason, "details": details, "evidence_count": len(observation.get("evidence", [])) if isinstance(observation, dict) and isinstance(observation.get("evidence"), list) else 0})
    indexed = {row["control_id"]: row for row in rows}
    low, high = observations.get("S1"), observations.get("S2")
    if indexed.get("S1", {}).get("status") == "PASS" and indexed.get("S2", {}).get("status") == "PASS" and low and high:
        low_metrics, high_metrics = low["metrics"], high["metrics"]
        if low_metrics["constraint_density"] >= high_metrics["constraint_density"] or low_metrics["choice_cardinality"] <= high_metrics["choice_cardinality"]:
            for cid in ("S1", "S2"):
                indexed[cid]["status"], indexed[cid]["reason"] = "FAIL", "KNOWN_LOW_HIGH_ORDERING_VIOLATION"
    counts = {status: sum(row["status"] == status for row in rows) for status in ("PASS", "FAIL", "BLOCKED")}
    gate_status = "PASS_SCOPED" if rows and counts["PASS"] == len(rows) else "BLOCKED"
    return {"schema_version": "apex44-scientific-control-report-v1", "evaluation_id": document.get("evaluation_id", "UNSPECIFIED"), "subject": document.get("subject") if isinstance(document.get("subject"), dict) else None, "contract_schema_version": contract.get("schema_version"), "acceptance_status": contract.get("acceptance_status", "UNSPECIFIED"), "control_count": len(rows), "summary": counts, "scientific_control_gate_status": gate_status, "release_promotion_authority": "NONE", "controls": rows, "interpretation_boundary": "PASS_SCOPED evaluates only these bounded controls for the identified subject against proposed thresholds. SHA-256 verifies bytes at a local evidence path only; it does not prove origin, independence, semantic identity, admissibility, or truth. The thresholds require preregistration review, and this gate never independently authorizes production release."}

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--observations", type=Path)
    parser.add_argument("--evidence-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        contract = json.loads(args.contract.read_text(encoding="utf-8"))
        document = json.loads(args.observations.read_text(encoding="utf-8")) if args.observations else {}
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    if not isinstance(contract, dict) or not isinstance(contract.get("controls"), list) or len(contract["controls"]) != 14:
        print("CONTRACT_ERROR: expected exactly 14 controls", file=sys.stderr)
        return 2
    report = evaluate(document, contract, args.evidence_root)
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0 if report["scientific_control_gate_status"] == "PASS_SCOPED" else 2

if __name__ == "__main__":
    raise SystemExit(main())
