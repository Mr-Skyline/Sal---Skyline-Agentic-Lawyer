"""Backward-compatible shim: re-export `sal.config` for legacy `from config import`."""
from __future__ import annotations

import sitepath

sitepath.ensure()

from sal.config import *  # noqa: F403
