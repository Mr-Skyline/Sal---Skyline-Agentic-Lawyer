"""
Fast import smoke test (no Streamlit run).

  py scripts/smoke_check.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
sys.path.insert(0, str(_PROJECT_ROOT))


def main() -> int:
    mods = [
        "src.sal.config",
        "src.sal.sal_prompt",
        "src.sal.analysis",
        "src.sal.evidence",
        "src.sal.draft",
        "src.sal.review_export",
        "src.sal.db",
        "src.sal.ingest",
        "src.sal.gmail_retry",
        "src.sal.logger_util",
        "src.sal.secrets_store",
        "src.sal.verify_setup",
        "src.sal.sync_worker",
    ]
    failed: list[tuple[str, str]] = []
    for m in mods:
        try:
            __import__(m)
        except Exception as e:
            failed.append((m, f"{type(e).__name__}: {e}"))
    if failed:
        for m, err in failed:
            print(f"FAIL {m}: {err}", file=sys.stderr)
        return 1
    print("OK:", ", ".join(mods))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
