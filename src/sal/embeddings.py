"""Text chunking and embedding generation for Track D semantic search."""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from .logger_util import log_event

EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_BASE_URL = os.environ.get("EMBEDDING_BASE_URL", "https://api.openai.com/v1")
EMBEDDING_API_KEY = os.environ.get("EMBEDDING_API_KEY", "") or os.environ.get("XAI_API_KEY", "")
CHUNK_MAX_TOKENS = int(os.environ.get("EMBEDDING_CHUNK_MAX_TOKENS", "500"))
CHUNK_OVERLAP_TOKENS = int(os.environ.get("EMBEDDING_CHUNK_OVERLAP_TOKENS", "50"))


def _approx_token_count(text: str) -> int:
    """Rough token estimate: ~4 chars per token for English text."""
    return max(1, len(text) // 4)


def chunk_text(
    text: str,
    *,
    max_tokens: int = 0,
    overlap_tokens: int = 0,
    prefix: str = "",
) -> list[str]:
    """Split *text* into overlapping chunks of approximately *max_tokens* size.

    Each chunk is prefixed with *prefix* if provided (e.g. subject line).
    Returns a list of chunk strings.  Empty text returns an empty list.
    """
    max_tokens = max_tokens or CHUNK_MAX_TOKENS
    overlap_tokens = overlap_tokens or CHUNK_OVERLAP_TOKENS

    if not text or not text.strip():
        return []

    max_chars = max_tokens * 4
    overlap_chars = overlap_tokens * 4

    full_text = text.strip()
    if _approx_token_count(full_text) <= max_tokens:
        chunk = f"{prefix}\n{full_text}".strip() if prefix else full_text
        return [chunk]

    paragraphs = re.split(r"\n\s*\n", full_text)

    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current) + len(para) + 1 <= max_chars:
            current = f"{current}\n{para}".strip() if current else para
        else:
            if current:
                chunk = f"{prefix}\n{current}".strip() if prefix else current
                chunks.append(chunk)
                if overlap_chars > 0 and len(current) > overlap_chars:
                    current = current[-overlap_chars:] + "\n" + para
                else:
                    current = para
            else:
                sentences = re.split(r"(?<=[.!?])\s+", para)
                for sent in sentences:
                    if len(current) + len(sent) + 1 <= max_chars:
                        current = f"{current} {sent}".strip() if current else sent
                    else:
                        if current:
                            chunk = f"{prefix}\n{current}".strip() if prefix else current
                            chunks.append(chunk)
                            if overlap_chars > 0 and len(current) > overlap_chars:
                                current = current[-overlap_chars:] + " " + sent
                            else:
                                current = sent
                        else:
                            chunk = f"{prefix}\n{sent[:max_chars]}".strip() if prefix else sent[:max_chars]
                            chunks.append(chunk)
                            current = ""

    if current.strip():
        chunk = f"{prefix}\n{current}".strip() if prefix else current
        chunks.append(chunk)

    return chunks


def chunk_hash(text: str) -> str:
    """Stable content hash for deduplication (16-char hex prefix of SHA-256)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def load_thread_archive(archive_path: Path) -> list[dict[str, Any]]:
    """Load a thread archive JSON file (as produced by sync_worker).

    Returns list of message dicts, or empty list on error.
    """
    if not archive_path.is_file():
        return []
    try:
        data = json.loads(archive_path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def chunks_from_thread_archive(
    archive_path: Path,
    *,
    max_tokens: int = 0,
    overlap_tokens: int = 0,
) -> list[dict[str, Any]]:
    """Generate embedding-ready chunks from a thread archive JSON file.

    Returns list of dicts with keys:
      text, content_hash, source_type, source_id, source_path, metadata
    """
    messages = load_thread_archive(archive_path)
    if not messages:
        return []

    thread_id = ""
    all_chunks: list[dict[str, Any]] = []

    for msg in messages:
        text = (msg.get("text") or "").strip()
        if not text:
            continue

        thread_id = msg.get("thread_id") or thread_id
        subject = (msg.get("subject") or "").strip()
        prefix = f"Subject: {subject}" if subject else ""

        text_chunks = chunk_text(
            text,
            max_tokens=max_tokens,
            overlap_tokens=overlap_tokens,
            prefix=prefix,
        )

        for chunk_text_str in text_chunks:
            all_chunks.append(
                {
                    "text": chunk_text_str,
                    "content_hash": chunk_hash(chunk_text_str),
                    "source_type": "gmail_thread",
                    "source_id": thread_id,
                    "source_path": str(archive_path),
                    "metadata": {
                        "subject": subject,
                        "sender": msg.get("sender", ""),
                        "date": msg.get("date", ""),
                        "message_id": msg.get("message_id", ""),
                    },
                }
            )

    return all_chunks


def generate_embeddings(
    texts: list[str],
    *,
    model: str = "",
    base_url: str = "",
    api_key: str = "",
) -> list[list[float]]:
    """Call an OpenAI-compatible embedding API.

    Returns list of embedding vectors.
    Raises ``ValueError`` if API key is not configured.
    Raises ``RuntimeError`` on API errors.
    """
    model = model or EMBEDDING_MODEL
    base_url = base_url or EMBEDDING_BASE_URL
    api_key = api_key or EMBEDDING_API_KEY

    if not api_key:
        raise ValueError("Set EMBEDDING_API_KEY or XAI_API_KEY for embedding generation.")

    if not texts:
        return []

    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url)

    try:
        response = client.embeddings.create(model=model, input=texts)
        sorted_data = sorted(response.data, key=lambda x: x.index)
        vectors = [item.embedding for item in sorted_data]

        log_event(
            "embeddings_generated",
            extra={
                "model": model,
                "count": len(texts),
                "dimensions": len(vectors[0]) if vectors else 0,
            },
        )
        return vectors
    except Exception as e:
        log_event("embeddings_error", error=str(e))
        raise RuntimeError(f"Embedding API error: {e}") from e
