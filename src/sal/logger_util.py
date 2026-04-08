"""Append-only JSONL log: queries, token usage, errors."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .config import LOG_FILE as _LOG_FILE_CONFIG

# Tests may patch this name with a str; normalize at use sites.
LOG_FILE: Union[Path, str] = _LOG_FILE_CONFIG


def _log_path() -> Path:
    return Path(LOG_FILE)

# When the log exceeds this size (bytes), rotate once to LOG_FILE + ".1" before appending.
_DEFAULT_MAX_LOG_BYTES = 10 * 1024 * 1024


def _maybe_rotate_jsonl_log() -> None:
    max_bytes = int(os.environ.get("SAL_LOG_JSONL_MAX_BYTES", str(_DEFAULT_MAX_LOG_BYTES)))
    if max_bytes <= 0:
        return
    try:
        lp = _log_path()
        if not lp.exists():
            return
        if lp.stat().st_size < max_bytes:
            return
        rotated = lp.with_name(lp.name + ".1")
        if rotated.exists():
            rotated.unlink()
        lp.rename(rotated)
    except OSError:
        pass


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
        _maybe_rotate_jsonl_log()
        with open(_log_path(), "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError:
        pass
