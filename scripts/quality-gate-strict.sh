#!/bin/bash
set -e
echo "=== APEX44 Quality Gate Strict ==="
python src/crypto/verify_quantum_gate.py || exit 1
echo "=== GATE PASSED ==="
