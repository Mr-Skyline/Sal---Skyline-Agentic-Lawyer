"""Append-only JSONL log: queries, token usage, errors."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from config import LOG_FILE

# Cap exception strings so pipeline failures cannot echo large evidence payloads into JSONL.
_MAX_ERROR_LOG_CHARS = 2000


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
        row["error"] = (
            error
            if len(error) <= _MAX_ERROR_LOG_CHARS
            else error[: _MAX_ERROR_LOG_CHARS - 1] + "…"
        )
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError:
        pass
