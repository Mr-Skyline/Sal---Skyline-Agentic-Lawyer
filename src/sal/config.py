"""Paths, API endpoints, and constants for Sal — Skyline Agentic Lawyer.

Canonical project root: INTENDED_PROJECT_ROOT (see below).
"""
import os
from pathlib import Path
from typing import Any

_ROOT_DIR = Path(__file__).resolve().parent.parent.parent  # src/sal/ → project root
try:
    from dotenv import load_dotenv

    load_dotenv(_ROOT_DIR / ".env")
except ImportError:
    pass

ROOT = _ROOT_DIR

# Only active project root for this machine — no second working copy (see README, verify_setup).
INTENDED_PROJECT_ROOT = Path(r"C:\Users\travi\Projects\AI Lawyer Build")

# Skyline multi-state: Grok infers `primary_state`; review files live under SKYLINE_REVIEW_DIR/<state>/.
JOB_SITE_STATE_CODES = ("CO", "FL", "AZ", "TX", "NE")
REVIEW_STATE_UNSPECIFIED = "_unspecified"


def normalize_primary_state(value: Any) -> str:
    """Return a canonical state code or "" if missing/invalid."""
    if value is None:
        return ""
    s = str(value).strip().upper()
    return s if s in JOB_SITE_STATE_CODES else ""


def review_state_subdir(canonical_code: str) -> str:
    """Folder name under SKYLINE_REVIEW_DIR for partitioned exports."""
    c = normalize_primary_state(canonical_code)
    return c if c else REVIEW_STATE_UNSPECIFIED

# Sal Phase 2 markdown exports (`review_export.py`). Override with absolute Windows path if needed.
_skyline_review = os.environ.get("SKYLINE_REVIEW_DIR", "").strip()
SKYLINE_REVIEW_DIR = (
    Path(os.path.expandvars(os.path.expanduser(_skyline_review))).resolve()
    if _skyline_review
    else (ROOT / "skyline_review").resolve()
)

CREDENTIALS_FILE = ROOT / "credentials.json"
TOKEN_FILE = ROOT / "token.pickle"

# Gmail OAuth loopback (Web clients must list each http://localhost:PORT/ you use in Google Cloud).
# Default 8765 avoids clashes with other tools that often bind 8090 on Windows.
OAUTH_LOCAL_PORT = int(os.environ.get("OAUTH_LOCAL_PORT", "8765"))
# If the first port is busy, try the next N-1 ports (register all of them as redirect URIs).
OAUTH_LOCAL_PORT_TRY_COUNT = max(
    1, min(20, int(os.environ.get("OAUTH_LOCAL_PORT_TRY_COUNT", "5")))
)
# If Cursor or another handler steals "default browser", set to 0 and paste the printed Google URL into Chrome/Edge.
_oauth_ob = os.environ.get("OAUTH_OPEN_BROWSER", "1").strip().lower()
OAUTH_OPEN_BROWSER = _oauth_ob not in ("0", "false", "no", "off")
# Must match an Authorized redirect URI exactly. Use "localhost" if Console only lists http://localhost:PORT/.
OAUTH_LOOPBACK_HOST = (
    os.environ.get("OAUTH_LOOPBACK_HOST", "127.0.0.1").strip() or "127.0.0.1"
)

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
]

GROK_BASE_URL = "https://api.x.ai/v1"
GROK_MODEL = "grok-4.20-0309-reasoning"

LOG_FILE = ROOT / "dispute_agent_log.jsonl"

API_MAX_RETRIES = 5
API_BASE_DELAY_SEC = 1.0

GMAIL_MAX_RETRIES = 5
GMAIL_RETRY_BASE_SEC = 1.0

# Dedicated agent mailbox + continuous ingest (sync_worker.py)
AGENT_GMAIL_ADDRESS = os.environ.get("AGENT_GMAIL_ADDRESS", "").strip()
CORRESPONDENCE_ARCHIVE_DIR = os.environ.get("CORRESPONDENCE_ARCHIVE_DIR", "").strip()
SYNC_POLL_INTERVAL_SEC = int(os.environ.get("SYNC_POLL_INTERVAL_SEC", "300"))
SYNC_NEWER_THAN_DAYS = int(os.environ.get("SYNC_NEWER_THAN_DAYS", "7"))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip() or os.environ.get(
    "SUPABASE_KEY", ""
).strip()
