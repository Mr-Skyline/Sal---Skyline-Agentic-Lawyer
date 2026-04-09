"""Track D: pgvector-backed semantic search for Sal embeddings."""
from __future__ import annotations

import json
from typing import Any, Optional

from .db import supabase_client
from .logger_util import log_event

EMBEDDINGS_TABLE = "sal_embeddings"


def upsert_chunks_with_embeddings(
    chunks: list[dict[str, Any]],
    vectors: list[list[float]],
) -> int:
    """Store chunk text + embedding vectors in Supabase pgvector table.

    Uses content_hash as unique key for dedup (upsert).
    Returns number of rows upserted. No-op if Supabase unconfigured.
    """
    if not chunks or not vectors or len(chunks) != len(vectors):
        return 0

    cli = supabase_client()
    if cli is None:
        return 0

    rows = []
    for chunk, vector in zip(chunks, vectors):
        rows.append({
            "content_hash": chunk["content_hash"],
            "source_type": chunk.get("source_type", "gmail_thread"),
            "source_id": chunk.get("source_id", ""),
            "source_path": chunk.get("source_path", ""),
            "chunk_text": chunk["text"],
            "metadata": json.dumps(chunk.get("metadata", {})),
            "embedding": vector,
        })

    try:
        cli.table(EMBEDDINGS_TABLE).upsert(
            rows, on_conflict="content_hash"
        ).execute()
        log_event(
            "vector_store_upsert",
            extra={"count": len(rows)},
        )
        return len(rows)
    except Exception as e:
        log_event(
            "vector_store_upsert_error",
            extra={"error_type": type(e).__name__, "count": len(rows)},
        )
        return 0


def semantic_search(
    query_embedding: list[float],
    *,
    limit: int = 10,
    source_type: Optional[str] = None,
    similarity_threshold: float = 0.0,
) -> list[dict[str, Any]]:
    """Find chunks most similar to the query embedding using cosine similarity.

    Returns list of dicts with: chunk_text, source_type, source_id, source_path,
    metadata, similarity score. Ordered by similarity descending.

    Returns empty list if Supabase is unconfigured or on error.
    """
    cli = supabase_client()
    if cli is None:
        return []

    try:
        params: dict[str, Any] = {
            "query_embedding": query_embedding,
            "match_count": limit,
            "match_threshold": similarity_threshold,
        }
        if source_type:
            params["filter_source_type"] = source_type

        result = cli.rpc("match_sal_embeddings", params).execute()
        return result.data or []
    except Exception as e:
        log_event(
            "vector_search_error",
            extra={"error_type": type(e).__name__},
        )
        return []


def get_embedding_stats() -> dict[str, Any]:
    """Return basic stats about the embeddings table.
    Returns empty dict if unconfigured."""
    cli = supabase_client()
    if cli is None:
        return {}

    try:
        result = cli.table(EMBEDDINGS_TABLE).select(
            "source_type", count="exact"
        ).execute()
        total = result.count or 0

        return {
            "total_chunks": total,
            "table": EMBEDDINGS_TABLE,
        }
    except Exception as e:
        log_event(
            "vector_stats_error",
            extra={"error_type": type(e).__name__},
        )
        return {}


def delete_source_embeddings(source_id: str) -> int:
    """Delete all embeddings for a given source (e.g., a thread_id).
    Returns count deleted. No-op if unconfigured."""
    cli = supabase_client()
    if cli is None:
        return 0

    try:
        result = cli.table(EMBEDDINGS_TABLE).delete().eq(
            "source_id", source_id
        ).execute()
        count = len(result.data or [])
        log_event(
            "vector_source_deleted",
            extra={"source_id": source_id, "count": count},
        )
        return count
    except Exception as e:
        log_event(
            "vector_delete_error",
            extra={"error_type": type(e).__name__, "source_id": source_id},
        )
        return 0
