"""Print redirect URIs for Google Cloud (Web client). Run: py print_redirect_uri.py"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from config import (  # noqa: E402
    OAUTH_LOCAL_PORT,
    OAUTH_LOCAL_PORT_TRY_COUNT,
    OAUTH_LOOPBACK_HOST,
)

ports = [OAUTH_LOCAL_PORT + i for i in range(OAUTH_LOCAL_PORT_TRY_COUNT)]

print(f"OAuth loopback host: {OAUTH_LOOPBACK_HOST} (set OAUTH_LOOPBACK_HOST in .env to change).\n")
print("Register these under Authorized redirect URIs:\n")
for p in ports:
    print(f"  http://{OAUTH_LOOPBACK_HOST}:{p}/")
oh = OAUTH_LOOPBACK_HOST
other = "localhost" if oh != "localhost" else "127.0.0.1"
print(f"\nAlso register the same ports for http://{other}:PORT/ if you switch hosts.\n")
print("\nFor full steps: py oauth_google_checklist.py\n")
