from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile


def load_module():
    path = Path(
        "APEX44/02-science/control_plane/scientific_contract.py"
    )
    spec = importlib.util.spec_from_file_location(
        "scientific_contract_test_module",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("module_load_failed")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_canonical_hash_is_deterministic():
    module = load_module()

    a = {
        "b": 2,
        "a": {
            "y": 1,
            "x": 3,
        },
    }

    b = {
        "a": {
            "x": 3,
            "y": 1,
        },
        "b": 2,
    }

    assert module.sha256_canonical(a) == module.sha256_canonical(b)


def test_hash_excludes_self_reference():
    module = load_module()

    contract = {
        "schema": module.SCHEMA_ID,
        "contract_id": "TEST",
        "question": "Q",
        "hypothesis": "H",
        "estimand": "E",
        "unit": "U",
        "source_manifest": {
            "path": "x",
            "sha256": "0" * 64,
        },
        "representation": {
            "path": "x",
            "status": "CANONICAL_CURRENT",
            "dimensions": [1, 1],
            "source_hash": "s",
            "B_hash": "b",
            "lock": True,
        },
        "allowed_specifications": ["spec"],
        "forbidden_adaptive_changes": [],
        "confirmation_policy": {},
        "claim_policy": {},
    }

    first = module.contract_hash(contract)
    contract["contract_hash"] = first

    assert module.contract_hash(contract) == first


def test_conflicted_representation_blocks_execution():
    module = load_module()

    contract = {
        "schema": module.SCHEMA_ID,
        "contract_id": "TEST-CONFLICT",
        "question": "Q",
        "hypothesis": "H",
        "estimand": "E",
        "unit": "U",
        "source_manifest": {
            "path": "x",
            "sha256": "0" * 64,
        },
        "representation": {
            "path": "x",
            "status": "CONFLICT",
            "dimensions": [1, 1],
            "source_hash": "s",
            "B_hash": "b",
            "lock": True,
        },
        "qac_provenance_status": "UNRESOLVED_PROVENANCE_CONFLICT",
        "allowed_specifications": ["spec"],
        "forbidden_adaptive_changes": ["adaptive change"],
        "confirmation_policy": {},
        "claim_policy": {},
    }

    contract["contract_hash"] = module.contract_hash(contract)

    result = module.validate_contract(contract)

    assert result["valid"] is True
    assert result["scientific_execution_allowed"] is False
    assert result["promotion_allowed"] is False


def test_real_contract_validates():
    module = load_module()

    path = Path(
        "APEX44/02-science/control_plane/contracts/"
        "scientific_inference_v0.1.json"
    )

    result = module.validate_file(path)

    assert result["valid"] is True
    assert result["promotion_allowed"] is False


print("TEST_MODULE_IMPORT=PASS")
test_canonical_hash_is_deterministic()
print("TEST_CANONICAL_HASH=PASS")
test_hash_excludes_self_reference()
print("TEST_SELF_HASH_EXCLUSION=PASS")
test_conflicted_representation_blocks_execution()
print("TEST_CONFLICT_BLOCK=PASS")
test_real_contract_validates()
print("TEST_REAL_CONTRACT=PASS")
