"""
Track E — Gmail Pub/Sub push-based sync (replaces polling for real-time inbox monitoring).

Architecture:
  Gmail watch API → Google Cloud Pub/Sub → Supabase Edge Function (webhook) → sync_worker --once

Setup:
  1. Enable Gmail API + Pub/Sub API in Google Cloud Console
  2. Create Pub/Sub topic: gmail-push-{project}
  3. Grant gmail-api-push@system.gserviceaccount.com publish permission on the topic
  4. Create Pub/Sub push subscription pointing to the Supabase Edge Function URL
  5. Deploy the Edge Function (gmail-push-handler)
  6. Call gmail_watch() to register the watch on the mailbox
  7. Set GMAIL_PUSH_ENABLED=1 in .env

  python gmail_push.py watch     # Register Gmail push watch (re-register every 7 days)
  python gmail_push.py stop      # Stop push notifications
  python gmail_push.py status    # Check current watch status
"""
from __future__ import annotations

import argparse
import os
import sys
import time

import sitepath

sitepath.ensure()

from dotenv import load_dotenv

from evidence import get_gmail_service
from logger_util import log_event
from sal.config import ROOT

load_dotenv(ROOT / ".env", override=True)

GMAIL_PUSH_ENABLED = os.environ.get("GMAIL_PUSH_ENABLED", "").strip().lower() in (
    "1",
    "true",
    "yes",
)
PUBSUB_TOPIC = os.environ.get(
    "GMAIL_PUBSUB_TOPIC", ""
).strip()
WATCH_LABEL_IDS = ["INBOX"]


def _require_enabled() -> None:
    if not GMAIL_PUSH_ENABLED:
        print(
            "Gmail push is disabled. Set GMAIL_PUSH_ENABLED=1 in .env to activate.",
            file=sys.stderr,
        )
        sys.exit(1)


def _require_topic() -> str:
    if not PUBSUB_TOPIC:
        print(
            "Set GMAIL_PUBSUB_TOPIC in .env (e.g. projects/my-project/topics/gmail-push)",
            file=sys.stderr,
        )
        sys.exit(1)
    return PUBSUB_TOPIC


def gmail_watch() -> dict:
    """Register Gmail push notifications via Pub/Sub watch."""
    topic = _require_topic()
    svc = get_gmail_service()
    body = {
        "topicName": topic,
        "labelIds": WATCH_LABEL_IDS,
        "labelFilterBehavior": "INCLUDE",
    }
    result = svc.users().watch(userId="me", body=body).execute()
    expiration = result.get("expiration", "unknown")
    history_id = result.get("historyId", "unknown")
    log_event(
        "gmail_push_watch_registered",
        extra={
            "topic": topic,
            "expiration": expiration,
            "history_id": history_id,
        },
    )
    print("Watch registered:")
    print(f"  Topic: {topic}")
    print(f"  Expiration: {expiration}")
    print(f"  History ID: {history_id}")
    exp_ts = int(expiration) / 1000 if expiration != "unknown" else 0
    if exp_ts:
        remaining = exp_ts - time.time()
        days = remaining / 86400
        print(f"  Expires in: {days:.1f} days")
        print("  Re-register before expiration (max 7 days).")
    return result


def gmail_stop() -> None:
    """Stop Gmail push notifications."""
    svc = get_gmail_service()
    svc.users().stop(userId="me", body={}).execute()
    log_event("gmail_push_watch_stopped")
    print("Watch stopped.")


def gmail_status() -> None:
    """Check current mailbox profile (historyId indicates last known state)."""
    svc = get_gmail_service()
    profile = svc.users().getProfile(userId="me").execute()
    print(f"Email: {profile.get('emailAddress')}")
    print(f"Messages: {profile.get('messagesTotal')}")
    print(f"History ID: {profile.get('historyId')}")
    print(f"Push enabled: {GMAIL_PUSH_ENABLED}")
    print(f"Pub/Sub topic: {PUBSUB_TOPIC or '(not set)'}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Track E — Gmail Pub/Sub push sync")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("watch", help="Register Gmail push watch")
    sub.add_parser("stop", help="Stop push notifications")
    sub.add_parser("status", help="Check current status")

    args = parser.parse_args()
    if args.command == "watch":
        _require_enabled()
        gmail_watch()
        return 0
    elif args.command == "stop":
        gmail_stop()
        return 0
    elif args.command == "status":
        gmail_status()
        return 0
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
