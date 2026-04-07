"""
Gmail OAuth file checks + what to do when Google says "blocked".

  py oauth_diagnose.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> None:
    cred_path = ROOT / "credentials.json"
    tok_path = ROOT / "token.pickle"

    print(f"Project folder: {ROOT}")
    print(f"credentials.json: {'ok' if cred_path.exists() else 'MISSING'}")
    print(f"token.pickle: {'exists' if tok_path.exists() else 'missing (expected until login works)'}\n")

    if not cred_path.exists():
        print("Add credentials.json from Google Cloud (Desktop app download is easiest).")
        sys.exit(1)

    try:
        data = json.loads(cred_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"credentials.json is not valid JSON: {e}")
        sys.exit(1)

    has_web = "web" in data
    has_installed = "installed" in data
    if not has_web and not has_installed:
        print('JSON must contain "web" and/or "installed".')
        sys.exit(1)

    if has_web and has_installed:
        print("WARNING: Both 'web' and 'installed' exist. The app uses WEB first (same as Google libraries).")
        print("Remove 'web' if you meant to use Desktop-only credentials.\n")

    if has_web:
        kind = "WEB application (redirect URIs must match Google Cloud Console exactly)"
        block = data["web"]
    else:
        kind = "DESKTOP app (recommended — dynamic localhost port, no redirect URI list)"
        block = data["installed"]

    print(f"OAuth client type in this file: {kind}\n")

    pid = (block.get("project_id") or "").strip()
    cid = (block.get("client_id") or "").strip()
    sec = (block.get("client_secret") or "").strip()
    if pid:
        print(f"project_id: {pid}")
    print(f"client_id: ...{cid[-24:]}" if len(cid) > 24 else f"client_id: {cid}")
    print(f"client_secret present: {bool(sec)} (length {len(sec)})\n")

    if not cid or not sec:
        print("client_id and client_secret must both be non-empty.")
        sys.exit(1)

    if pid:
        print("Open in browser (same Google account you use for Cloud Console):\n")
        print(
            f"  OAuth consent screen: https://console.cloud.google.com/apis/credentials/consent?project={pid}"
        )
        print(
            f"  Credentials list: https://console.cloud.google.com/apis/credentials?project={pid}"
        )
        print(
            f"  Gmail API: https://console.cloud.google.com/apis/library/gmail.googleapis.com?project={pid}\n"
        )

    if has_web:
        print("Web client: run  py oauth_google_checklist.py  and copy every redirect URI into Console.\n")

    print(
        "If Google says BLOCKED or you cannot click Continue:\n"
        "  - Internal app: sign in only with a user in YOUR Workspace org (same company as the Cloud project).\n"
        "  - Testing mode + External: OAuth consent screen -> add your email under Test users.\n"
        "  - 'App not verified' + gmail.modify: click Advanced -> Go to ... (unsafe) if Google shows it,\n"
        "    or keep app in Testing and add yourself as a test user.\n"
        "  - Workspace admin may block 'Less secure' / third-party OAuth; admin must allow the app or Gmail API.\n"
    )

    print(
        "Fastest technical fix when Web keeps failing:\n"
        "  Create NEW OAuth client type **Desktop app** -> Download JSON -> replace credentials.json\n"
        "  (file should have only 'installed' { ... }, no 'web' block) -> delete token.pickle -> py oauth_login.py\n"
    )


if __name__ == "__main__":
    main()
