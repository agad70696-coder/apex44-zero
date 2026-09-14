from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA_ID = (
    "scientific-inference-control-plane-synthetic-crosscheck-v0.1"
)


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def implementation_a(matrix: list[list[int]]) -> dict[str, Any]:
    if not matrix:
        return {
            "rows": 0,
            "cols": 0,
            "nnz": 0,
            "row_sums": [],
            "col_sums": [],
        }

    rows = len(matrix)
    cols = len(matrix[0])

    if any(len(row) != cols for row in matrix):
        raise ValueError("ragged_matrix")

    row_sums = [
        sum(row)
        for row in matrix
    ]

    col_sums = [
        sum(matrix[row][col] for row in range(rows))
        for col in range(cols)
    ]

    nnz = sum(
        1
        for row in matrix
        for value in row
        if value != 0
    )

    return {
        "rows": rows,
        "cols": cols,
        "nnz": nnz,
        "row_sums": row_sums,
        "col_sums": col_sums,
    }


def implementation_b(matrix: list[list[int]]) -> dict[str, Any]:
    rows = len(matrix)

    if rows == 0:
        cols = 0
    else:
        cols = len(matrix[0])

    if any(len(row) != cols for row in matrix):
        raise ValueError("ragged_matrix")

    row_sums = []
    nnz = 0

    for row in matrix:
        total = 0
        for value in row:
            total += value
            if value != 0:
                nnz += 1
        row_sums.append(total)

    col_sums = []

    for col in range(cols):
        total = 0
        for row in range(rows):
            total += matrix[row][col]
        col_sums.append(total)

    return {
        "rows": rows,
        "cols": cols,
        "nnz": nnz,
        "row_sums": row_sums,
        "col_sums": col_sums,
    }


def independently_hash_result(result: dict[str, Any]) -> str:
    payload = json.dumps(
        result,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return sha256_bytes(payload)


def run_crosscheck() -> dict[str, Any]:
    synthetic_cases = {
        "empty": [],
        "single": [[1]],
        "binary": [
            [1, 0, 1],
            [0, 1, 0],
            [1, 0, 0],
        ],
        "weighted": [
            [2, 0, 3],
            [0, 4, 0],
            [5, 0, 1],
        ],
        "zero_row": [
            [0, 0, 0],
            [1, 0, 2],
        ],
    }

    cases: dict[str, Any] = {}
    all_equal = True

    for name, matrix in synthetic_cases.items():
        result_a = implementation_a(matrix)
        result_b = implementation_b(matrix)

        equal = result_a == result_b
        all_equal = all_equal and equal

        cases[name] = {
            "result_a": result_a,
            "result_b": result_b,
            "equal": equal,
            "hash_a": independently_hash_result(result_a),
            "hash_b": independently_hash_result(result_b),
        }

    return {
        "schema": SCHEMA_ID,
        "case_count": len(synthetic_cases),
        "cases": cases,
        "all_equal": all_equal,
        "valid": all_equal,
    }
