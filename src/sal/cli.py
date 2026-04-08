"""Console entry points (see pyproject.toml `[project.scripts]`)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _run_py(cwd: Path, *args: str) -> int:
    return subprocess.call([sys.executable, *args], cwd=str(cwd))


def skyline_streamlit() -> None:
    """Run Streamlit UI from repo root."""
    root = _repo_root()
    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
    raise SystemExit(
        _run_py(root, "-m", "streamlit", "run", str(root / "main.py"))
    )


def skyline_verify_setup() -> None:
    root = _repo_root()
    raise SystemExit(_run_py(root, str(root / "verify_setup.py"), *sys.argv[1:]))


def skyline_smoke() -> None:
    root = _repo_root()
    raise SystemExit(_run_py(root, str(root / "smoke_check.py"), *sys.argv[1:]))


def skyline_env_check() -> None:
    root = _repo_root()
    raise SystemExit(_run_py(root, str(root / "env_check.py"), *sys.argv[1:]))
