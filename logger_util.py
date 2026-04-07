"""Append-only JSONL log: queries, token usage, errors."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from config import LOG_FILE


def log_event(
    event: str,
    *,
    extra: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> None:
    row: Dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
    }
    if extra:
        row["extra"] = extra
    if error:
        row["error"] = error
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError:
        pass
