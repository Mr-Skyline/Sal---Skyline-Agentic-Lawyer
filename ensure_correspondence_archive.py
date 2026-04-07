"""
Create a local correspondence_archive/ folder and append CORRESPONDENCE_ARCHIVE_DIR to .env
if unset (for sync_worker). Safe to re-run.

  .venv\\Scripts\\python.exe ensure_correspondence_archive.py
"""
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent
    archive = root / "correspondence_archive"
    archive.mkdir(parents=True, exist_ok=True)

    env_path = root / ".env"
    if not env_path.is_file():
        print(
            "No .env found — create from .env.example first, then re-run.",
            file=sys.stderr,
        )
        return 1

    text = env_path.read_text(encoding="utf-8")
    has_value = False
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.upper().startswith("CORRESPONDENCE_ARCHIVE_DIR="):
            val = s.split("=", 1)[1].strip().strip('"').strip("'")
            if val:
                has_value = True
            break

    if has_value:
        print(f"CORRESPONDENCE_ARCHIVE_DIR already set in .env — archive dir: {archive}")
        return 0

    with open(env_path, "a", encoding="utf-8") as f:
        if text and not text.endswith("\n"):
            f.write("\n")
        f.write(
            "\n# Local Gmail thread JSON archive (sync_worker); override with a UNC if needed\n"
        )
        f.write(f"CORRESPONDENCE_ARCHIVE_DIR={archive}\n")
    print(f"Appended CORRESPONDENCE_ARCHIVE_DIR={archive}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
