"""Illustrative medicine-evidence gate.

This module is a software/testing example, not a clinical decision-support system. Its tiny
allow-list must not be used to recommend, prescribe, or validate real patient treatment.
Unknown medications and unsupported contexts return False so they can be reviewed by a
qualified clinician.
"""
from __future__ import annotations

import hashlib
import json
import time
from typing import Any


def personal_hash(data: str) -> str:
    return hashlib.sha3_256(data.encode("utf-8")).hexdigest()


class PersonalizedMedicineEvidence:
    """Record sample prescription data and apply a deliberately narrow test policy."""

    HIGH_RISK_COMBINATIONS = {
        "CYP2D6-poor": {"codeine", "tramadol"},
        "HLA-B*58:01": {"allopurinol"},
    }
    # This single test-fixture rule is not a complete dosage guideline.
    DEMO_ALLOWLIST_MAX_DOSE_MG = {"paracetamol": 1000.0}

    def __init__(self, patient_id: str, genome_marker: str, age: int, weight: float) -> None:
        if not patient_id or not genome_marker:
            raise ValueError("patient_id and genome_marker are required")
        if isinstance(age, bool) or age <= 0:
            raise ValueError("age must be a positive integer")
        if weight <= 0:
            raise ValueError("weight must be positive")
        self.patient_id = patient_id
        self.genome_marker = genome_marker
        self.age = age
        self.weight = float(weight)
        self.created_at = time.time()
        self.prescriptions: list[dict[str, Any]] = []
        self.base_hash = personal_hash(
            json.dumps(
                {
                    "patient_id": patient_id,
                    "genome_marker": genome_marker,
                    "age": age,
                    "weight": self.weight,
                    "created_at": self.created_at,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        )

    def add_prescription(self, drug: str, dose_mg: float, evidence_score: float) -> None:
        """Append synthetic medication evidence; evidence_score is a 0-100 record field."""
        name = drug.strip().lower() if isinstance(drug, str) else ""
        if not name:
            raise ValueError("drug name is required")
        if dose_mg <= 0:
            raise ValueError("dose_mg must be positive")
        if not 0 <= evidence_score <= 100:
            raise ValueError("evidence_score must be between 0 and 100")
        item = {
            "drug": name,
            "dose_mg": float(dose_mg),
            "evidence_score": float(evidence_score),
        }
        item["record_hash"] = personal_hash(
            json.dumps(item, sort_keys=True, separators=(",", ":"))
        )
        self.prescriptions.append(item)

    def is_treatment_safe(self) -> bool:
        """Return whether data passes this narrow fixture policy, not a clinical judgment."""
        if not self.prescriptions or self.weight <= 0 or self.age <= 0:
            return False

        high_risk = self.HIGH_RISK_COMBINATIONS.get(self.genome_marker, set())
        for item in self.prescriptions:
            drug = item["drug"]
            if drug in high_risk:
                return False
            max_demo_dose = self.DEMO_ALLOWLIST_MAX_DOSE_MG.get(drug)
            if max_demo_dose is None:
                return False
            if item["dose_mg"] > max_demo_dose or item["evidence_score"] < 50:
                return False
        return True
