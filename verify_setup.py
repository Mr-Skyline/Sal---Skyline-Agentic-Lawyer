"""
Check local setup without starting Streamlit.

  py verify_setup.py                # print status
  py verify_setup.py --strict       # exit 1 if Gmail + Grok prerequisites missing
  py verify_setup.py --supabase-ping  # also test DB read; exit 2 if ping fails when flag is set
"""
from __future__ import annotations

import sitepath

sitepath.ensure()

import argparse
import os
import sys
from typing import List, NamedTuple, Tuple

from dotenv import load_dotenv


class SetupStatus(NamedTuple):
    """Printed status lines plus readiness flags."""

    lines: List[str]
    grok_and_credentials_ok: bool
    gmail_api_ok: bool


def run_checks() -> SetupStatus:
    """
    grok_and_credentials_ok: XAI key + credentials.json (can start OAuth).
    gmail_api_ok: above + token.pickle (Gmail API calls will work).
    """
    from sal.config import (
        AGENT_GMAIL_ADDRESS,
        CORRESPONDENCE_ARCHIVE_DIR,
        CREDENTIALS_FILE,
        INTENDED_PROJECT_ROOT,
        ROOT,
        SKYLINE_REVIEW_DIR,
        SUPABASE_KEY,
        SUPABASE_URL,
        TOKEN_FILE,
    )

    load_dotenv(ROOT / ".env", override=True)

    lines: List[str] = []
    lines.append(f"Project folder: {ROOT}")
    try:
        intended_env = os.environ.get("INTENDED_PROJECT_ROOT", "").strip()
        if intended_env and ROOT.resolve() != INTENDED_PROJECT_ROOT.resolve():
            lines.append(
                f"  WARNING: not canonical root (expected {INTENDED_PROJECT_ROOT} per INTENDED_PROJECT_ROOT); "
                "open that folder in Cursor and terminals, or unset INTENDED_PROJECT_ROOT to silence this."
            )
    except OSError:
        lines.append("  NOTE: Could not resolve project path.")
    vi = sys.version_info
    lines.append(f"  Python: {vi.major}.{vi.minor}.{vi.micro}")
    if vi.major > 3 or (vi.major == 3 and vi.minor > 12):
        lines.append(
            "  Python note: 3.11-3.12 recommended for smoothest pip wheels (OCR/Supabase extras)."
        )
    cred = CREDENTIALS_FILE.exists()
    lines.append(f"  credentials.json: {'ok' if cred else 'MISSING'}")
    tok = TOKEN_FILE.exists()
    lines.append(
        f"  token.pickle: {'ok' if tok else 'missing (run py oauth_login.py from this folder)'}"
    )
    lines.append(f"  .env file: {'ok' if (ROOT / '.env').exists() else 'optional if keys are in environment'}")
    xai = bool(os.environ.get("XAI_API_KEY"))
    lines.append(f"  XAI_API_KEY: {'ok' if xai else 'MISSING'}")
    ocr = bool(os.environ.get("ZHIPU_API_KEY") or os.environ.get("GLMOCR_API_KEY"))
    lines.append(f"  OCR key (ZHIPU/GLMOCR): {'ok' if ocr else 'optional unless using screenshots'}")
    if ocr:
        try:
            import glmocr  # noqa: F401

            lines.append("  glmocr package: import ok")
        except ImportError:
            lines.append(
                "  glmocr package: MISSING (pip install -r requirements-ocr.txt)"
            )
    lines.append(f"  SKYLINE_REVIEW_DIR: {SKYLINE_REVIEW_DIR}")
    try:
        SKYLINE_REVIEW_DIR.mkdir(parents=True, exist_ok=True)
        test = SKYLINE_REVIEW_DIR / ".write_test_verify_setup"
        test.write_text("", encoding="utf-8")
        test.unlink()
        lines.append("  SKYLINE_REVIEW_DIR writable: ok")
    except OSError as e:
        lines.append(f"  SKYLINE_REVIEW_DIR writable: FAIL ({e})")

    sb_env = bool(SUPABASE_URL and SUPABASE_KEY)
    lines.append(
        f"  Supabase (metadata upserts): {'env ok' if sb_env else 'optional (not configured)'}"
    )
    if sb_env:
        try:
            import supabase  # noqa: F401

            lines.append("  supabase package: import ok")
            lines.append(
                "  supabase schema: apply supabase_schema.sql (threads + skyline_review_exports audit)"
            )
        except ImportError:
            lines.append(
                "  supabase package: MISSING (pip install -r requirements-supabase.txt)"
            )

    agent_ok = bool(AGENT_GMAIL_ADDRESS)
    arch_ok = bool(CORRESPONDENCE_ARCHIVE_DIR)
    if agent_ok and arch_ok:
        lines.append("  sync_worker env: ok (agent mailbox + archive dir)")
    elif not agent_ok and not arch_ok:
        lines.append("  sync_worker env: optional (not configured)")
    elif not agent_ok:
        lines.append(
            "  sync_worker env: incomplete - missing AGENT_GMAIL_ADDRESS "
            "(archive dir is set; set both for py sync_worker.py)"
        )
    else:
        lines.append(
            "  sync_worker env: incomplete - missing CORRESPONDENCE_ARCHIVE_DIR "
            "(agent mailbox is set; set both for py sync_worker.py)"
        )

    grok_and_credentials_ok = xai and cred
    gmail_api_ok = grok_and_credentials_ok and tok
    return SetupStatus(lines, grok_and_credentials_ok, gmail_api_ok)


def run_supabase_ping() -> Tuple[List[str], bool]:
    """
    SELECT against correspondence_threads (limit 1). No secrets printed.
    Returns (lines, ok). ok is False when Supabase is configured but unreachable / mis-schemed.
    """
    lines: List[str] = []
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = (
        os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        or os.environ.get("SUPABASE_KEY", "").strip()
    )
    if not url or not key:
        lines.append("  supabase-ping: skipped (Supabase URL/key not set)")
        return lines, True
    try:
        from supabase import create_client
    except ImportError:
        lines.append(
            "  supabase-ping: FAIL (supabase package missing; pip install -r requirements-supabase.txt)"
        )
        return lines, False
    try:
        cli = create_client(url, key)
        cli.table("correspondence_threads").select("gmail_thread_id").limit(1).execute()
        lines.append("  supabase-ping: ok (correspondence_threads readable)")
        return lines, True
    except Exception as e:
        hint = str(e).replace("\n", " ")[:160]
        lines.append(
            f"  supabase-ping: FAIL ({type(e).__name__}) — {hint} "
            "(apply supabase_schema.sql in Supabase SQL editor?)"
        )
        return lines, False


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify Dispute Agent Elite local setup.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 unless Grok, credentials.json, and token.pickle are ready (full Gmail path).",
    )
    parser.add_argument(
        "--supabase-ping",
        action="store_true",
        help="After status lines, run a read against correspondence_threads; exit 1 if configured but ping fails.",
    )
    args = parser.parse_args()
    status = run_checks()
    out_lines = list(status.lines)
    if args.supabase_ping:
        ping_lines, ping_ok = run_supabase_ping()
        out_lines.extend(ping_lines)
        if not ping_ok:
            print("\n".join(out_lines))
            print(
                "\n--supabase-ping failed: fix package, .env, or schema (see supabase_schema.sql).",
                file=sys.stderr,
            )
            sys.exit(1)
    print("\n".join(out_lines))
    if args.strict and not status.gmail_api_ok:
        print(
            "\nStrict mode: need XAI_API_KEY, credentials.json, and token.pickle "
            "(run py oauth_login.py from this folder if token is missing).",
            file=sys.stderr,
        )
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
