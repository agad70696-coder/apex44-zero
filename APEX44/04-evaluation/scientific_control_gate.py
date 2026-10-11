"""Fail-closed evaluator for the fourteen APEX44 scientific-control contracts.

Thresholds are proposed operational values pending preregistration review. PASS_SCOPED
validates bounded controls only; it neither proves a claim nor authorizes release.
"""
from __future__ import annotations
import argparse, json, math, re, sys
from pathlib import Path
from typing import Any

HERE=Path(__file__).resolve().parent
DEFAULT_CONTRACT=HERE/"scientific_control_contract.json"
SHA256=re.compile(r"^[0-9a-f]{64}$")
COMMIT=re.compile(r"^[0-9a-f]{40}$")

def number(x: Any)->bool:
    return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)

def text(x: Any)->bool:
    return isinstance(x,str) and bool(x.strip())

def subject_error(doc: dict[str,Any])->str|None:
    s=doc.get("subject")
    if not isinstance(s,dict): return "SUBJECT_PROVENANCE_MISSING"
    if not isinstance(s.get("commit_sha"),str) or not COMMIT.fullmatch(s["commit_sha"]): return "SUBJECT_COMMIT_SHA_INVALID"
    if not isinstance(s.get("dataset_sha256"),str) or not SHA256.fullmatch(s["dataset_sha256"]): return "SUBJECT_DATASET_SHA256_INVALID"
    if not text(s.get("model_id")): return "SUBJECT_MODEL_ID_MISSING"
    return None

def evidence_error(obs: dict[str,Any])->str|None:
    ev=obs.get("evidence")
    if not isinstance(ev,list) or not ev: return "EVIDENCE_MISSING"
    for i,item in enumerate(ev):
        if not isinstance(item,dict) or not text(item.get("source")) or not text(item.get("role")): return f"EVIDENCE_ITEM_{i}_SOURCE_OR_ROLE_MISSING"
        if not isinstance(item.get("sha256"),str) or not SHA256.fullmatch(item["sha256"]): return f"EVIDENCE_ITEM_{i}_SHA256_INVALID"
    return None

def kendall_tau(a: dict[str,float],b: dict[str,float])->float:
    keys=sorted(set(a)&set(b)); concordance=pairs=0
    for i,x in enumerate(keys):
        for y in keys[i+1:]:
            pairs+=1; product=(a[x]-a[y])*(b[x]-b[y])
            concordance+=1 if product>0 else -1 if product<0 else 0
    return concordance/pairs if pairs else 0.0

def assess(c: dict[str,Any],m: dict[str,Any])->tuple[str,str,dict[str,Any]]:
    cid,t=c["id"],c["acceptance"]
    if cid in ("S1","S2"):
        d,n=m["constraint_density"],m["choice_cardinality"]
        if not number(d) or not 0<=d<=1 or not isinstance(n,int) or isinstance(n,bool) or n<1: return "BLOCKED","METRIC_TYPE_OR_RANGE_INVALID",{}
        ok=(d<=t["constraint_density_max"] and n>=t["choice_cardinality_min"]) if cid=="S1" else (d>=t["constraint_density_min"] and n<=t["choice_cardinality_max"])
        return ("PASS" if ok else "FAIL","ACCEPTANCE_MET" if ok else "ACCEPTANCE_NOT_MET",{"constraint_density":d,"choice_cardinality":n})
    if cid=="S3":
        p,s=m["probabilities"],m["surprisal_bits"]
        if not isinstance(p,list) or not isinstance(s,list) or len(p)!=len(s) or len(p)<t["minimum_points"]: return "BLOCKED","PROBABILITY_SERIES_INCOMPLETE",{}
        if any(not number(v) or v<=0 or v>1 for v in p) or any(not number(v) for v in s): return "BLOCKED","PROBABILITY_OR_SURPRISAL_INVALID",{}
        err=max(abs(v+math.log2(q)) for q,v in zip(p,s)); ordered=sorted(zip(p,s))
        monotonic=all(ordered[i][1]>ordered[i+1][1] for i in range(len(ordered)-1))
        ok=err<=t["absolute_tolerance"] and monotonic
        return ("PASS" if ok else "FAIL","CALIBRATION_MET" if ok else "CALIBRATION_MISMATCH",{"max_absolute_error_bits":err,"strict_inverse_order":monotonic})
    if cid=="S4":
        pairs=m["matched_score_pairs"]
        if not isinstance(pairs,list) or len(pairs)<t["minimum_pairs"]: return "BLOCKED","MATCHED_PAIRS_INCOMPLETE",{}
        deltas=[]
        for pair in pairs:
            if not isinstance(pair,dict) or not number(pair.get("short_score")) or not number(pair.get("padded_score")): return "BLOCKED","MATCHED_PAIR_INVALID",{}
            deltas.append(abs(pair["short_score"]-pair["padded_score"]))
        mx=max(deltas); ok=mx<=t["maximum_absolute_score_delta"]
        return ("PASS" if ok else "FAIL","LENGTH_INVARIANCE_MET" if ok else "LENGTH_CONFOUNDING_DETECTED",{"max_absolute_delta":mx,"pair_count":len(pairs)})
    if cid=="S5":
        base,curve=m["baseline_score"],m["perturbation_curve"]
        if not number(base) or not isinstance(curve,list): return "BLOCKED","PERTURBATION_CURVE_INVALID",{}
        by={}
        for point in curve:
            if not isinstance(point,dict) or not isinstance(point.get("noise_percent"),int) or not number(point.get("score")): return "BLOCKED","PERTURBATION_POINT_INVALID",{}
            level=point["noise_percent"]
            if level in by: return "BLOCKED","DUPLICATE_NOISE_LEVEL",{}
            by[level]=point["score"]
        if not set(t["required_noise_percent_levels"]).issubset(by): return "BLOCKED","REQUIRED_NOISE_LEVEL_MISSING",{"levels":sorted(by)}
        if abs(by[0]-base)>t["absolute_tolerance"]: return "FAIL","ZERO_NOISE_BASELINE_MISMATCH",{}
        mx=max(abs(v-base) for v in by.values()); ok=mx<=t["maximum_absolute_score_delta"]
        return ("PASS" if ok else "FAIL","SENSITIVITY_WITHIN_BUDGET" if ok else "SENSITIVITY_BUDGET_EXCEEDED",{"max_absolute_delta":mx,"levels":sorted(by)})
    if cid=="S6":
        rs=m["scores_by_representation"]; req=t["required_representations"]
        if not isinstance(rs,dict) or any(k not in rs for k in req): return "BLOCKED","REPRESENTATION_MISSING",{}
        for k in req:
            if not isinstance(rs[k],dict) or len(rs[k])<t["minimum_candidates"] or any(not text(a) or not number(b) for a,b in rs[k].items()): return "BLOCKED",f"REPRESENTATION_{k}_SCORES_INVALID",{}
        shared=set.intersection(*(set(rs[k]) for k in req))
        if len(shared)<t["minimum_candidates"]: return "BLOCKED","SHARED_CANDIDATE_SET_TOO_SMALL",{}
        taus={f"{a}:{b}":kendall_tau({k:rs[a][k] for k in shared},{k:rs[b][k] for k in shared}) for i,a in enumerate(req) for b in req[i+1:]}
        mn=min(taus.values()); ok=mn>=t["minimum_pairwise_kendall_tau"]
        return ("PASS" if ok else "FAIL","RANK_STABILITY_MET" if ok else "REPRESENTATION_RANK_SHIFT",{"pairwise_kendall_tau":taus,"minimum_pairwise_kendall_tau":mn})
    if cid=="S9":
        f,seed,detected,rate=(m[k] for k in ("artifact_fixture_id","generator_seed","injected_artifact_detected","clean_control_false_positive_rate"))
        if not text(f) or not text(str(seed)) or not isinstance(detected,bool) or not number(rate) or not 0<=rate<=1: return "BLOCKED","GENERATOR_BIAS_METRIC_INVALID",{}
        ok=detected and rate<=t["clean_control_false_positive_rate_max"]
        return ("PASS" if ok else "FAIL","ARTIFACT_CONTROL_MET" if ok else "GENERATOR_BIAS_CONTROL_FAILED",{"artifact_fixture_id":f,"generator_seed":seed,"clean_control_false_positive_rate":rate})
    if cid=="S10":
        keys=("leakage_injected_detected","promotion_allowed_on_leaked_fixture","clean_fixture_not_flagged")
        if any(not isinstance(m.get(k),bool) for k in keys): return "BLOCKED","LEAKAGE_METRIC_INVALID",{}
        ok=m[keys[0]] and not m[keys[1]] and m[keys[2]]
        return ("PASS" if ok else "FAIL","LEAKAGE_SENTINEL_ENFORCED" if ok else "LEAKAGE_SENTINEL_FAILED",{k:m[k] for k in keys})
    if cid=="S11":
        legal,illegal=m["legal_transform_results"],m["illegal_transform_results"]
        if not isinstance(legal,list) or not isinstance(illegal,list) or len(legal)<t["minimum_legal_cases"] or len(illegal)<t["minimum_illegal_cases"]: return "BLOCKED","TRANSFORM_CASES_INCOMPLETE",{}
        if any(not isinstance(x,dict) or not text(x.get("transform_id")) or not isinstance(x.get("scope_preserved"),bool) for x in legal): return "BLOCKED","LEGAL_TRANSFORM_CASE_INVALID",{}
        if any(not isinstance(x,dict) or not text(x.get("transform_id")) or not isinstance(x.get("rejected"),bool) for x in illegal): return "BLOCKED","ILLEGAL_TRANSFORM_CASE_INVALID",{}
        ok=all(x["scope_preserved"] for x in legal) and all(x["rejected"] for x in illegal)
        return ("PASS" if ok else "FAIL","TRANSFORM_POLICY_ENFORCED" if ok else "TRANSFORM_POLICY_VIOLATION",{"legal_cases":len(legal),"illegal_cases":len(illegal)})
    if cid=="S12":
        a,b,p=(m[k] for k in ("candidate_score","strongest_baseline_score","adjusted_p_value"))
        if any(not number(v) for v in (a,b,p)) or not 0<=p<=1: return "BLOCKED","TOURNAMENT_METRIC_INVALID",{}
        advantage=a-b; ok=advantage>=t["minimum_advantage"] and p<=t["maximum_adjusted_p_value"]
        return ("PASS" if ok else "FAIL","ALTERNATIVE_ADVANTAGE_ESTABLISHED" if ok else "ALTERNATIVE_ADVANTAGE_NOT_ESTABLISHED",{"advantage":advantage,"adjusted_p_value":p})
    if cid=="S13":
        hs,promoted=m["hidden_constraints"],m["unverified_promoted_as_fact"]
        if not isinstance(hs,list) or not isinstance(promoted,bool): return "BLOCKED","HIDDEN_CONSTRAINT_METRIC_INVALID",{}
        if any(not isinstance(x,dict) or x.get("status")!="CANDIDATE" or not text(x.get("provenance_ref")) for x in hs): return "FAIL","HIDDEN_CONSTRAINT_PROVENANCE_OR_STATUS_VIOLATION",{}
        ok=len(hs)>=t["minimum_candidates"] and not promoted
        return ("PASS" if ok else "FAIL","HYPOTHESIS_BOUNDARY_PRESERVED" if ok else "HIDDEN_CONSTRAINT_BOUNDARY_FAILED",{"candidate_count":len(hs),"unverified_promoted_as_fact":promoted})
    if cid=="S14":
        variants,promoted=m["annotation_variant_scores"],m["claim_promoted"]
        if not isinstance(variants,dict) or not isinstance(promoted,bool) or any(not text(k) or not number(v) for k,v in variants.items()): return "BLOCKED","MULTIVERSE_METRIC_INVALID",{}
        if len(variants)<t["minimum_variants"]: return "BLOCKED","ANNOTATION_VARIANTS_INCOMPLETE",{}
        spread=max(variants.values())-min(variants.values()); ok=spread<=t["maximum_claim_score_spread"] or not promoted
        return ("PASS" if ok else "FAIL","MULTIVERSE_DISAGREEMENT_HANDLED" if ok else "CLAIM_PROMOTED_DESPITE_DISAGREEMENT",{"variant_count":len(variants),"score_spread":spread,"claim_promoted":promoted})
    if cid=="S15":
        keys=("critical_failure_injected","promotion_blocked","override_authority_checked")
        if any(not isinstance(m.get(k),bool) for k in keys): return "BLOCKED","KILL_SWITCH_METRIC_INVALID",{}
        ok=all(m[k] for k in keys)
        return ("PASS" if ok else "FAIL","KILL_SWITCH_ENFORCED" if ok else "KILL_SWITCH_BYPASS_OR_FAILURE",{k:m[k] for k in keys})
    if cid=="S16":
        keys=("failure_detected","failure_type","location","evidence_ref","reproduction_command")
        if not isinstance(m["failure_detected"],bool) or any(not text(m[k]) for k in keys[1:]): return "BLOCKED","FAILURE_PROFILE_INCOMPLETE",{}
        ok=m["failure_detected"] and m["failure_type"] in t["allowed_failure_types"]
        return ("PASS" if ok else "FAIL","FAILURE_TYPED_AND_LOCALIZED" if ok else "FAILURE_PROFILE_UNUSABLE",{k:m[k] for k in keys})
    return "BLOCKED","NO_EVALUATOR_FOR_CONTROL",{}

def evaluate(document: dict[str,Any],contract: dict[str,Any])->dict[str,Any]:
    document=document if isinstance(document,dict) else {}; controls=contract.get("controls",[]); raw=document.get("observations",[])
    observations={}; duplicates=set()
    if isinstance(raw,list):
        for o in raw:
            if isinstance(o,dict) and text(o.get("control_id")):
                cid=o["control_id"]
                if cid in observations: duplicates.add(cid)
                observations[cid]=o
    se=subject_error(document); rows=[]
    for c in controls:
        cid=c["id"]; o=observations.get(cid); m=o.get("metrics") if isinstance(o,dict) else None
        if cid in duplicates: status,reason,details="BLOCKED","DUPLICATE_CONTROL_OBSERVATION",{}
        elif se: status,reason,details="BLOCKED",se,{}
        elif o is None: status,reason,details="BLOCKED","OBSERVATION_MISSING",{}
        elif evidence_error(o): status,reason,details="BLOCKED",evidence_error(o),{}
        elif not isinstance(m,dict): status,reason,details="BLOCKED","METRICS_MISSING",{}
        elif [k for k in c.get("metrics_required",[]) if k not in m]: status,reason,details="BLOCKED","REQUIRED_METRICS_MISSING",{"missing":[k for k in c["metrics_required"] if k not in m]}
        else:
            try: status,reason,details=assess(c,m)
            except (KeyError,TypeError,ValueError,OverflowError): status,reason,details="BLOCKED","METRICS_SCHEMA_INVALID",{}
        rows.append({"control_id":cid,"name":c["name"],"status":status,"reason":reason,"details":details,"evidence_count":len(o.get("evidence",[])) if isinstance(o,dict) and isinstance(o.get("evidence"),list) else 0})
    by={x["control_id"]:x for x in rows}; low=observations.get("S1"); high=observations.get("S2")
    if by.get("S1",{}).get("status")=="PASS" and by.get("S2",{}).get("status")=="PASS" and low and high:
        lm,hm=low["metrics"],high["metrics"]
        if lm["constraint_density"]>=hm["constraint_density"] or lm["choice_cardinality"]<=hm["choice_cardinality"]:
            for cid in ("S1","S2"): by[cid]["status"]="FAIL"; by[cid]["reason"]="KNOWN_LOW_HIGH_ORDERING_VIOLATION"
    counts={s:sum(x["status"]==s for x in rows) for s in ("PASS","FAIL","BLOCKED")}
    status="PASS_SCOPED" if rows and counts["PASS"]==len(rows) else "BLOCKED"
    return {"schema_version":"apex44-scientific-control-report-v1","evaluation_id":document.get("evaluation_id","UNSPECIFIED"),"subject":document.get("subject") if isinstance(document.get("subject"),dict) else None,"contract_schema_version":contract.get("schema_version"),"acceptance_status":contract.get("acceptance_status","UNSPECIFIED"),"control_count":len(rows),"summary":counts,"scientific_control_gate_status":status,"release_promotion_authority":"NONE","controls":rows,"interpretation_boundary":"PASS_SCOPED validates only these bounded controls for the identified subject and evidence against proposed operational thresholds. It does not prove scientific truth; the thresholds require preregistration review and this gate never independently authorizes production release."}

def main(argv: list[str]|None=None)->int:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT); p.add_argument("--observations",type=Path); p.add_argument("--output",type=Path); a=p.parse_args(argv)
    try: c=json.loads(a.contract.read_text(encoding="utf-8")); d=json.loads(a.observations.read_text(encoding="utf-8")) if a.observations else {}
    except (OSError,json.JSONDecodeError) as e: print(f"INPUT_ERROR: {type(e).__name__}: {e}",file=sys.stderr); return 2
    if not isinstance(c,dict) or not isinstance(c.get("controls"),list) or len(c["controls"])!=14: print("CONTRACT_ERROR: expected exactly 14 controls",file=sys.stderr); return 2
    report=evaluate(d,c); out=json.dumps(report,ensure_ascii=False,indent=2)+"\n"
    if a.output: a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(out,encoding="utf-8")
    print(out,end=""); return 0 if report["scientific_control_gate_status"]=="PASS_SCOPED" else 2

if __name__=="__main__": raise SystemExit(main())
