"""Write API keys to .env and Gmail OAuth JSON to credentials.json (local disk only)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import set_key


def _valid_google_oauth_client(data: Dict[str, Any]) -> bool:
    for key in ("installed", "web"):
        block = data.get(key)
        if isinstance(block, dict) and block.get("client_id") and block.get(
            "client_secret"
        ):
            return True
    return False


def save_api_keys_to_dotenv(
    root: Path,
    *,
    xai_api_key: Optional[str] = None,
    zhipu_api_key: Optional[str] = None,
) -> List[str]:
    """Upsert keys into root/.env. Empty strings are skipped. Returns keys written."""
    env_path = root / ".env"
    env_path.parent.mkdir(parents=True, exist_ok=True)

    written: List[str] = []
    if xai_api_key and xai_api_key.strip():
        set_key(str(env_path), "XAI_API_KEY", xai_api_key.strip(), quote_mode="never")
        written.append("XAI_API_KEY")
    if zhipu_api_key and zhipu_api_key.strip():
        set_key(str(env_path), "ZHIPU_API_KEY", zhipu_api_key.strip(), quote_mode="never")
        written.append("ZHIPU_API_KEY")
    return written


def save_gmail_credentials_json(root: Path, raw: bytes) -> None:
    """Validate and write Google Cloud OAuth client JSON to credentials.json."""
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ValueError("File is not valid UTF-8 JSON.") from e
    if not _valid_google_oauth_client(data):
        raise ValueError(
            "Expected Google OAuth client JSON (Desktop app) with "
            "'installed' or 'web' containing client_id and client_secret."
        )
    dest = root / "credentials.json"
    dest.write_bytes(raw)
