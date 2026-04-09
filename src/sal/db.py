"""Optional Supabase persistence for ingested thread metadata and review-export audit rows."""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Dict, Optional

from .logger_util import log_event


@lru_cache(maxsize=1)
def _cached_supabase_client():
    """Cached Supabase client. Returns None if not configured."""
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


def supabase_client():
    """Return cached client or None if not configured."""
    return _cached_supabase_client()


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


def batch_upsert_correspondence_threads(rows: list[Dict[str, Any]]) -> int:
    """Upsert multiple rows into correspondence_threads. Returns count of rows sent.
    No-op if Supabase unset. Logs on errors but doesn't raise."""
    if not rows:
        return 0
    cli = supabase_client()
    if cli is None:
        return 0
    try:
        cli.table("correspondence_threads").upsert(rows).execute()
        return len(rows)
    except Exception as e:
        log_event(
            "supabase_batch_upsert_skipped",
            extra={
                "error_type": type(e).__name__,
                "row_count": len(rows),
            },
        )
        return 0


def get_correspondence_thread(gmail_thread_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a single thread by Gmail thread ID. Returns None if not found or Supabase unconfigured."""
    cli = supabase_client()
    if cli is None:
        return None
    try:
        result = (
            cli.table("correspondence_threads")
            .select("*")
            .eq("gmail_thread_id", gmail_thread_id)
            .limit(1)
            .execute()
        )
        rows = result.data or []
        return rows[0] if rows else None
    except Exception as e:
        log_event(
            "supabase_thread_query_error",
            extra={"error_type": type(e).__name__, "gmail_thread_id": gmail_thread_id},
        )
        return None


def list_review_exports(
    *,
    primary_state: Optional[str] = None,
    limit: int = 50,
) -> list[Dict[str, Any]]:
    """List recent review export audit rows. Filter by state if provided."""
    cli = supabase_client()
    if cli is None:
        return []
    try:
        query = (
            cli.table("skyline_review_exports")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
        )
        if primary_state:
            query = query.eq("primary_state", primary_state.strip().upper())
        result = query.execute()
        return result.data or []
    except Exception as e:
        log_event(
            "supabase_review_exports_query_error",
            extra={"error_type": type(e).__name__},
        )
        return []


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
