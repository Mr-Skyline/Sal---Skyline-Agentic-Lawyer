"""Optional Supabase persistence for ingested thread metadata and review-export audit rows."""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

from logger_util import log_event


def supabase_client():
    """Return client or None if not configured."""
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = (
        os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        or os.environ.get("SUPABASE_KEY", "").strip()
    )
    if not url or not key:
        return None
    try:
        from supabase import create_client
    except ImportError:
        return None
    return create_client(url, key)


def upsert_correspondence_thread(row: Dict[str, Any]) -> None:
    """Upsert one row into correspondence_threads. No-op if Supabase unset; logs on API/schema errors."""
    cli = supabase_client()
    if cli is None:
        return
    try:
        cli.table("correspondence_threads").upsert(row).execute()
    except Exception as e:
        log_event(
            "supabase_correspondence_upsert_skipped",
            extra={
                "error_type": type(e).__name__,
                "gmail_thread_id": row.get("gmail_thread_id"),
            },
        )


def insert_review_export_meta(
    *,
    primary_state: Optional[str],
    state_subdir: str,
    file_name: str,
) -> None:
    """
    Append-only audit row when a review Markdown file is written.
    No claim text, email, or API keys — folder + filename + optional state code only.
    """
    cli = supabase_client()
    if cli is None:
        return
    ps = (primary_state or "").strip().upper() or None
    row = {
        "primary_state": ps,
        "state_subdir": state_subdir,
        "file_name": file_name,
    }
    try:
        cli.table("skyline_review_exports").insert(row).execute()
    except Exception as e:
        log_event(
            "supabase_review_export_insert_skipped",
            extra={
                "error_type": type(e).__name__,
                "file_name": file_name,
            },
        )
