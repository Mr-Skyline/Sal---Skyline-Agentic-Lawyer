"""
Quick Grok / Sal env sanity check without printing secrets.

  py env_check.py
  .venv\\Scripts\\python.exe env_check.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _ascii_path(p: Path, root: Path) -> str:
    """Console-safe path (Windows cp1252 often mangles en-dash in filenames)."""
    try:
        s = str(p.resolve().relative_to(root.resolve()))
    except ValueError:
        s = str(p.resolve())
    return s.encode("ascii", "replace").decode("ascii")


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root))
    try:
        from dotenv import load_dotenv

        load_dotenv(root / ".env", override=True)
    except ImportError:
        pass

    lines: list[str] = []
    lines.append(f"Project: {root}")
    lines.append(f"  .env present: {'yes' if (root / '.env').exists() else 'no'}")

    xai = bool(os.environ.get("XAI_API_KEY", "").strip())
    lines.append(
        f"  XAI_API_KEY loaded: {'yes' if xai else 'NO (set in .env or environment)'}"
    )

    cred = (root / "credentials.json").exists()
    lines.append(f"  credentials.json: {'yes' if cred else 'no'}")

    try:
        from src.sal.sal_prompt import default_sal_prompt_path, load_sal_behavioral_text

        p = default_sal_prompt_path()
        body = load_sal_behavioral_text()
        lines.append(f"  Sal prompt file: {_ascii_path(p, root)} (exists={'yes' if p.is_file() else 'no'})")
        if len(body) < 500:
            lines.append(
                "  Sal behavioral text: MISSING or too short (check SAL_PROMPT_PATH or default file)"
            )
        else:
            lines.append(f"  Sal behavioral text: ok ({len(body)} chars)")
    except OSError as e:
        lines.append(f"  Sal prompt check: {e}")

    print("\n".join(lines))
    return 0 if xai else 1


if __name__ == "__main__":
    sys.exit(main())
