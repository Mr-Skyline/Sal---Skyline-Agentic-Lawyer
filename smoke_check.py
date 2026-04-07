"""
Fast import smoke test (no Streamlit run).

  .venv\\Scripts\\python.exe smoke_check.py
  py smoke_check.py
"""
from __future__ import annotations

import sys


def main() -> int:
    mods = [
        "config",
        "sal_prompt",
        "analysis",
        "evidence",
        "draft",
        "review_export",
        "db",
        "ingest",
        "gmail_retry",
        "logger_util",
        "secrets_store",
        "verify_setup",
        "sync_worker",
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
