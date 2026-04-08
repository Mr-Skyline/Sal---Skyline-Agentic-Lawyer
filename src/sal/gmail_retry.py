"""Exponential backoff for transient Gmail API errors."""
from __future__ import annotations

import random
import time
from typing import Any

from googleapiclient.errors import HttpError

from .config import GMAIL_RETRY_BASE_SEC, GMAIL_MAX_RETRIES


def gmail_execute(request: Any, max_retries: int | None = None) -> Any:
    """Call request.execute() with retries on 429 / 5xx."""
    attempts = max_retries if max_retries is not None else GMAIL_MAX_RETRIES
    last_err: HttpError | None = None
    for attempt in range(attempts):
        try:
            return request.execute()
        except HttpError as e:
            last_err = e
            status = getattr(e.resp, "status", None) or 0
            if status not in (429, 500, 502, 503) or attempt >= attempts - 1:
                raise
            delay = GMAIL_RETRY_BASE_SEC * (2**attempt) + random.uniform(0, 0.4)
            time.sleep(delay)
    assert last_err is not None
    raise last_err
