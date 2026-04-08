"""
Ingest Gmail threads (e.g. where the agent mailbox is on To/Cc) into JSON archives
and optionally Supabase. Used by sync_worker.py for continuous monitoring.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .config import ROOT, SYNC_NEWER_THAN_DAYS
from .db import upsert_correspondence_thread
from .evidence import fetch_messages_for_evidence
from .gmail_retry import gmail_execute
from .logger_util import log_event


def format_sync_summary(
    summary: Dict[str, Any],
    agent_email: str,
    cycle_number: int = 0,
) -> Dict[str, Any]:
    """Enrich a sync_cc_threads_once summary with operator-friendly fields."""
    return {
        **summary,
        "agent_email": agent_email,
        "cycle": cycle_number,
        "status": "ok" if summary.get("archived", 0) >= 0 else "error",
        "human_summary": (
            f"Cycle {cycle_number}: "
            f"{summary.get('threads_seen', 0)} threads seen, "
            f"{summary.get('archived', 0)} archived, "
            f"{summary.get('skipped', 0)} unchanged"
        ),
    }


def cc_monitor_gmail_query(agent_email: str, newer_than_days: Optional[int] = None) -> str:
    """Gmail search: messages involving this address recently."""
    days = newer_than_days if newer_than_days is not None else SYNC_NEWER_THAN_DAYS
    return f"(cc:{agent_email} OR to:{agent_email}) newer_than:{days}d"


def fetch_thread_evidence(
    service,
    thread_id: str,
    max_messages: int = 80,
) -> Tuple[List[Dict[str, Any]], str]:
    """Load all messages in a thread; target_email unused when thread_id is set."""
    return fetch_messages_for_evidence(
        service,
        "me",
        "",
        thread_id=thread_id,
        max_messages=max_messages,
    )


def list_thread_ids(service, q: str, max_results: int = 50) -> List[str]:
    lst = gmail_execute(
        service.users().threads().list(
            userId="me",
            q=q,
            maxResults=max_results,
        )
    )
    return [t["id"] for t in (lst.get("threads") or []) if t.get("id")]


def _thread_latest_internal_date(service, thread_id: str) -> Tuple[int, str]:
    thr = gmail_execute(
        service.users().threads().get(userId="me", id=thread_id, format="full")
    )
    messages = thr.get("messages") or []
    if not messages:
        return 0, ""
    newest = max(int(m.get("internalDate", 0)) for m in messages)
    # Subject from first message headers (best-effort)
    first_id = messages[0]["id"]
    full = gmail_execute(
        service.users().messages().get(userId="me", id=first_id, format="metadata")
    )
    subj = ""
    for h in full.get("payload", {}).get("headers") or []:
        if (h.get("name") or "").lower() == "subject":
            subj = h.get("value") or ""
            break
    return newest, subj


def archive_thread_json(
    service,
    thread_id: str,
    archive_dir: Path,
) -> Path:
    archive_dir.mkdir(parents=True, exist_ok=True)
    items, _ = fetch_thread_evidence(service, thread_id)
    out = archive_dir / f"{thread_id}.json"
    out.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def load_sync_state(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"threads": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"threads": {}}


def save_sync_state(path: Path, state: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(state, indent=2, ensure_ascii=False)
    fd, tmp_path = tempfile.mkstemp(
        suffix=".tmp",
        prefix=path.name + ".",
        dir=path.parent,
        text=False,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def sync_cc_threads_once(
    service,
    agent_email: str,
    archive_dir: Path,
    state_path: Path,
    *,
    newer_than_days: Optional[int] = None,
    max_threads: int = 40,
) -> Dict[str, Any]:
    """
    One poll cycle: find threads matching CC/To monitor query, archive new/updated.
    Returns summary counts for logging.
    """
    q = cc_monitor_gmail_query(agent_email, newer_than_days)
    thread_ids = list_thread_ids(service, q, max_results=max_threads)
    state = load_sync_state(state_path)
    threads_map: Dict[str, int] = state.setdefault("threads", {})

    archived = 0
    skipped = 0
    for tid in thread_ids:
        newest, subject = _thread_latest_internal_date(service, tid)
        if newest == 0:
            skipped += 1
            continue
        old = int(threads_map.get(tid, 0))
        if newest <= old:
            skipped += 1
            continue
        path = archive_thread_json(service, tid, archive_dir)
        threads_map[tid] = newest
        archived += 1
        upsert_correspondence_thread(
            {
                "gmail_thread_id": tid,
                "subject": subject[:500] if subject else None,
                "last_message_internal_date": newest,
                "archive_path": str(path.resolve()),
            }
        )

    save_sync_state(state_path, state)
    log_event(
        "ingest_sync_once",
        extra={
            "query": q,
            "thread_count": len(thread_ids),
            "archived": archived,
            "skipped": skipped,
        },
    )
    return {
        "query": q,
        "threads_seen": len(thread_ids),
        "archived": archived,
        "skipped": skipped,
    }


def preview_sync_cc_threads(
    service,
    agent_email: str,
    state_path: Path,
    *,
    newer_than_days: Optional[int] = None,
    max_threads: int = 40,
) -> Dict[str, Any]:
    """
    Same discovery as sync_cc_threads_once but no archive writes, no state file updates, no Supabase.
    For operator verification and Task Scheduler smoke tests.
    """
    q = cc_monitor_gmail_query(agent_email, newer_than_days)
    thread_ids = list_thread_ids(service, q, max_results=max_threads)
    state = load_sync_state(state_path)
    threads_map: Dict[str, int] = state.get("threads") or {}

    would_archive = 0
    would_skip = 0
    rows: List[Dict[str, Any]] = []
    for tid in thread_ids:
        newest, subject = _thread_latest_internal_date(service, tid)
        subj_short = (subject or "")[:120]
        if newest == 0:
            would_skip += 1
            rows.append(
                {
                    "thread_id": tid,
                    "subject": subj_short,
                    "action": "skip",
                    "reason": "empty thread / no internalDate",
                }
            )
            continue
        old = int(threads_map.get(tid, 0))
        if newest <= old:
            would_skip += 1
            rows.append(
                {
                    "thread_id": tid,
                    "subject": subj_short,
                    "action": "skip",
                    "reason": "not newer than last synced internalDate",
                }
            )
        else:
            would_archive += 1
            rows.append(
                {
                    "thread_id": tid,
                    "subject": subj_short,
                    "action": "would_archive",
                    "reason": "new or updated since last sync",
                }
            )

    log_event(
        "ingest_sync_preview",
        extra={
            "query": q,
            "thread_count": len(thread_ids),
            "would_archive": would_archive,
            "would_skip": would_skip,
        },
    )
    return {
        "query": q,
        "threads_seen": len(thread_ids),
        "would_archive": would_archive,
        "would_skip": would_skip,
        "rows": rows,
    }


def default_state_path() -> Path:
    return ROOT / "correspondence_sync_state.json"
