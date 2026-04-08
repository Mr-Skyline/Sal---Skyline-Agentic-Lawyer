"""
Print what Google Cloud must allow for this app (no secrets).
Run from the project folder: py oauth_google_checklist.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from src.sal.config import (  # noqa: E402
    CREDENTIALS_FILE,
    OAUTH_LOCAL_PORT,
    OAUTH_LOCAL_PORT_TRY_COUNT,
    OAUTH_LOOPBACK_HOST,
)


def _gmail_link(pid: str) -> str:
    return (
        "https://console.cloud.google.com/apis/library/gmail.googleapis.com"
        f"?project={pid}"
    )


def _desktop_escape() -> None:
    print("--- Easiest fix if Web keeps failing (redirect_uri_mismatch) ---\n")
    print("Create a NEW OAuth client of type **Desktop app** (same Google Cloud project):\n")
    print("  Google Cloud -> APIs & Services -> Credentials -> Create Credentials ->")
    print("  OAuth client ID -> Application type: **Desktop app** -> Create ->")
    print("  **Download JSON** -> save as credentials.json in this folder (replace the old file).\n")
    print("Then run: python scripts/oauth_login.py\n")
    print("The app uses a random free loopback port (Desktop client); you do not list")
    print("http://127.0.0.1:8765/ etc. in the Console for that client.\n")


def main() -> None:
    if not CREDENTIALS_FILE.exists():
        print(f"Missing {CREDENTIALS_FILE.name}")
        sys.exit(1)
    raw = json.loads(CREDENTIALS_FILE.read_text(encoding="utf-8"))
    if "web" not in raw and "installed" not in raw:
        print("credentials.json must contain a 'web' or 'installed' object.")
        sys.exit(1)

    block = raw.get("web") or raw.get("installed")
    cid = block.get("client_id", "(missing)")
    pid = block.get("project_id", "(missing)")

    print("=== Google Cloud: what to verify ===\n")
    print(f"Project ID: {pid}")
    print(f"OAuth Client ID (must match Credentials row you edit): {cid}\n")

    if "installed" in raw and "web" not in raw:
        print("Your credentials.json is for a **Desktop** OAuth client.\n")
        print("1) Same project -> Enable Gmail API if needed:")
        if pid and pid != "(missing)":
            print(f"   {_gmail_link(pid)}\n")
        print("2) OAuth consent: Internal = only your Workspace org; External + test users if needed.\n")
        print("3) Run: python scripts/oauth_login.py (leave terminal open until done).\n")
        return

    ports = [OAUTH_LOCAL_PORT + i for i in range(OAUTH_LOCAL_PORT_TRY_COUNT)]

    print("Your credentials.json is for a **Web application** OAuth client.\n")
    print("1) APIs & Services -> Credentials -> that OAuth 2.0 Client ID\n")

    print("2) Authorized redirect URIs - add EVERY line (exact, trailing /).")
    print("   NOT under Authorized JavaScript origins.\n")
    print("   Required (app uses this host):")
    for p in ports:
        print(f"     http://{OAUTH_LOOPBACK_HOST}:{p}/")
    print("\n   Recommended (localhost):")
    for p in ports:
        print(f"     http://localhost:{p}/")
    print("\n   Save, wait ~1 minute.\n")

    if pid and pid != "(missing)":
        print("3) Enable Gmail API in the SAME project:\n")
        print(f"   {_gmail_link(pid)}\n")

    print("4) OAuth consent screen: Internal is OK for same-Workspace users.\n")
    print("5) Run: python scripts/oauth_login.py\n")
    _desktop_escape()


if __name__ == "__main__":
    main()
