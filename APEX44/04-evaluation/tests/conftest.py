from __future__ import annotations

import sys
from pathlib import Path

COMPUTATION_DIR = Path(__file__).resolve().parents[2] / "03-computation"
if str(COMPUTATION_DIR) not in sys.path:
    sys.path.insert(0, str(COMPUTATION_DIR))
