"""Hash-backed record of model predictions with conservative review flags.

A review flag is a configured heuristic, not proof that a prediction is false or fraudulent.
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from typing import Any


def predict_hash(data: str) -> str:
    return hashlib.sha3_256(data.encode("utf-8")).hexdigest()


class PredictiveEvidence:
    """Store synthetic prediction records and detect later record mutation."""

    def __init__(self, model_id: str, dataset_hash: str, phenomenon: str) -> None:
        if not model_id or not dataset_hash or not phenomenon:
            raise ValueError("model_id, dataset_hash, and phenomenon must be non-empty")
        self.model_id = model_id
        self.dataset_hash = dataset_hash
        self.phenomenon = phenomenon
        self.created_at = time.time()
        self.base_hash = predict_hash(
            json.dumps(
                {
                    "model_id": model_id,
                    "dataset_hash": dataset_hash,
                    "phenomenon": phenomenon,
                    "created_at": self.created_at,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        self.predictions: list[dict[str, Any]] = []

    def add_prediction(self, prediction: str, probability: float, impact: str) -> dict[str, Any]:
        if not prediction or not impact:
            raise ValueError("prediction and impact must be non-empty")
        if isinstance(probability, bool) or not isinstance(probability, (float, int)):
            raise TypeError("probability must be numeric")
        if not math.isfinite(float(probability)) or not 0.0 <= probability <= 1.0:
            raise ValueError("probability must be finite and between 0 and 1")
        timestamp = time.time()
        payload = {
            "model_id": self.model_id,
            "dataset_hash": self.dataset_hash,
            "phenomenon": self.phenomenon,
            "prediction": prediction,
            "probability": float(probability),
            "impact": impact,
            "timestamp": timestamp,
            "requires_review": (
                float(probability) >= 1.0
                or (float(probability) > 0.99 and impact.casefold() in {"high", "critical"})
            ),
        }
        payload["record_hash"] = predict_hash(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
        )
        self.predictions.append(payload)
        return payload.copy()

    @staticmethod
    def verify_prediction(record: dict[str, Any]) -> bool:
        if not isinstance(record, dict):
            return False
        supplied_hash = record.get("record_hash")
        if not isinstance(supplied_hash, str):
            return False
        payload = {key: value for key, value in record.items() if key != "record_hash"}
        try:
            expected = predict_hash(
                json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
            )
        except (TypeError, ValueError):
            return False
        return supplied_hash == expected
