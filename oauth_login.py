r"""
Gmail OAuth **outside Streamlit** (recommended if token.pickle never appears).

Streamlit reruns can interrupt the local OAuth server; this script runs one clean flow.

  cd /d "C:\Users\travi\Projects\AI Lawyer Build"
  py oauth_login.py

Removes existing token.pickle first, then opens the browser (or prints the URL if OAUTH_OPEN_BROWSER=0).
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env", override=True)

    tok = ROOT / "token.pickle"
    if tok.exists():
        tok.unlink()
        print("Removed old token.pickle")

    from config import CREDENTIALS_FILE, OAUTH_OPEN_BROWSER, TOKEN_FILE
    from evidence import get_gmail_service

    if not CREDENTIALS_FILE.exists():
        raise SystemExit(f"Missing credentials.json:\n  {CREDENTIALS_FILE.resolve()}")

    if OAUTH_OPEN_BROWSER:
        print(
            "A browser window should open. Sign in with your Workspace agent account.\n"
            "If the wrong app opens (e.g. Cursor), set OAUTH_OPEN_BROWSER=0 in .env and paste the "
            "printed https://accounts.google.com/... link into Chrome or Edge.\n"
            f"Token file will be:\n  {TOKEN_FILE.resolve()}\n"
        )
    else:
        print(
            "OAUTH_OPEN_BROWSER=0: copy the Google URL from the line below into Chrome or Edge.\n"
            f"Token file will be:\n  {TOKEN_FILE.resolve()}\n"
        )
    svc = get_gmail_service()
    if not TOKEN_FILE.exists():
        raise SystemExit(
            "OAuth did not create token.pickle. Common causes:\n"
            "  - Browser closed before 'Allow'\n"
            "  - Wrong browser opened → OAUTH_OPEN_BROWSER=0 in .env, paste URL into Chrome/Edge\n"
            "  - redirect_uri_mismatch → create OAuth client type **Desktop app** in Google Cloud\n"
            "  - Wrong Google Cloud project / client id vs secret mismatch\n"
        )
    prof = svc.users().getProfile(userId="me").execute()
    print("Success. Signed in as:", prof.get("emailAddress", "?"))


if __name__ == "__main__":
    main()
