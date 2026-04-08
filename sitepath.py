"""Ensure `src/` is on `sys.path` for runs without `pip install -e .` (repo root on path)."""
from __future__ import annotations

import sys
from pathlib import Path


def ensure() -> None:
    root = Path(__file__).resolve().parent
    src = root / "src"
    if src.is_dir():
        s = str(src)
        if s not in sys.path:
            sys.path.insert(0, s)
