"""
Continuous Gmail ingest for a dedicated agent inbox (CC/To monitoring).

  python -m src.sal.sync_worker              # loop: poll every SYNC_POLL_INTERVAL_SEC
  python -m src.sal.sync_worker --once       # single cycle (good for Task Scheduler)
  python -m src.sal.sync_worker --dry-run    # list threads that would archive/skip; no disk writes

Requires: OAuth token for the agent Gmail account and AGENT_GMAIL_ADDRESS.
CORRESPONDENCE_ARCHIVE_DIR is required for normal sync, not for --dry-run.

Run from the project root that contains credentials.json and token.pickle (same folder as main.py).

State file correspondence_sync_state.json is updated atomically (temp + replace).
Loop mode uses exponential backoff between errors, capped by SYNC_WORKER_BACKOFF_CAP_SEC.
Set SYNC_WORKER_MAX_CONSECUTIVE_ERRORS>0 to exit after that many failures in a row.
--once exits with code 1 if the sync cycle raises.
SIGINT/SIGTERM set a shutdown flag; the main loop exits gracefully on the next wait.
"""
from __future__ import annotations

import argparse
import os
import signal
import sys
import threading
from pathlib import Path

from dotenv import load_dotenv

from .config import ROOT
from .evidence import get_gmail_service
from .ingest import default_state_path, preview_sync_cc_threads, sync_cc_threads_once
from .logger_util import log_event

_shutdown = threading.Event()


def _handle_signal(signum, frame):
    _shutdown.set()


signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


def main() -> None:
    # Do not override existing os.environ (tests, Task Scheduler, one-off exports win over .env).
    load_dotenv(ROOT / ".env", override=False)

    parser = argparse.ArgumentParser(description="Gmail CC/thread sync worker")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single sync cycle then exit",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print threads that would archive or skip; no archive, state, or Supabase writes",
    )
    args = parser.parse_args()

    agent = os.environ.get("AGENT_GMAIL_ADDRESS", "").strip()
    if not agent:
        print("Set AGENT_GMAIL_ADDRESS in .env (the dedicated agent mailbox).", file=sys.stderr)
        sys.exit(1)

    state_path = default_state_path()
    interval = int(os.environ.get("SYNC_POLL_INTERVAL_SEC", "300"))
    backoff_cap = max(30, int(os.environ.get("SYNC_WORKER_BACKOFF_CAP_SEC", "300")))
    max_consec = int(os.environ.get("SYNC_WORKER_MAX_CONSECUTIVE_ERRORS", "0"))

    archive_raw = os.environ.get("CORRESPONDENCE_ARCHIVE_DIR", "").strip()
    if not args.dry_run and not archive_raw:
        print(
            "Set CORRESPONDENCE_ARCHIVE_DIR in .env (folder or UNC for archives).",
            file=sys.stderr,
        )
        sys.exit(1)

    archive_dir = Path(archive_raw) if archive_raw else Path(".")

    print(f"Agent mailbox: {agent}")
    if args.dry_run:
        print("Mode: DRY-RUN (no writes)")
    else:
        print(f"Archive dir: {archive_dir}")
    print(f"State file (read for preview): {state_path}")
    if not args.dry_run:
        print(f"Interval sec: {interval}")
    if not args.dry_run and not args.once:
        print(f"Backoff cap sec: {backoff_cap}")
        if max_consec > 0:
            print(f"Max consecutive errors (then exit): {max_consec}")

    if args.dry_run:
        try:
            service = get_gmail_service()
            prev = preview_sync_cc_threads(service, agent, state_path)
            print(f"Gmail query: {prev['query']}")
            print(
                f"Preview: seen={prev['threads_seen']} would_archive={prev['would_archive']} "
                f"would_skip={prev['would_skip']}"
            )
            for r in prev["rows"]:
                tid = r["thread_id"]
                tid_show = tid if len(tid) <= 20 else f"{tid[:18]}.."
                print(f"  [{r['action']}] {tid_show} | {r['subject']!r} | {r['reason']}")
        except Exception as e:
            log_event("sync_worker_dry_run_error", error=str(e))
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    consecutive = 0
    while True:
        try:
            service = get_gmail_service()
            summary = sync_cc_threads_once(service, agent, archive_dir, state_path)
            print(
                f"Synced: seen={summary['threads_seen']} archived={summary['archived']} "
                f"skipped={summary['skipped']}"
            )
            consecutive = 0
        except Exception as e:
            consecutive += 1
            log_event(
                "sync_worker_error",
                error=str(e),
                extra={"consecutive_failures": consecutive},
            )
            print(f"Error ({consecutive}): {e}", file=sys.stderr)
            if max_consec > 0 and consecutive >= max_consec:
                print(
                    f"Exiting: {consecutive} consecutive errors "
                    f"(SYNC_WORKER_MAX_CONSECUTIVE_ERRORS={max_consec}).",
                    file=sys.stderr,
                )
                sys.exit(1)
            if args.once:
                sys.exit(1)
            delay = min(
                backoff_cap,
                int(30 * (2 ** min(consecutive - 1, 6))),
            )
            if _shutdown.wait(timeout=delay):
                log_event("sync_worker_shutdown", extra={"phase": "error_backoff"})
                break
            continue

        if args.once:
            break
        if _shutdown.wait(timeout=max(30, interval)):
            log_event("sync_worker_shutdown", extra={"phase": "main_loop"})
            break

    sys.exit(0)


if __name__ == "__main__":
    main()
