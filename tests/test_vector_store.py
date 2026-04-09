"""Tests for src.sal.vector_store — pgvector storage layer (no live Supabase)."""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from src.sal.db import _cached_supabase_client
from src.sal.vector_store import (
    delete_source_embeddings,
    get_embedding_stats,
    semantic_search,
    upsert_chunks_with_embeddings,
)


@pytest.fixture(autouse=True)
def _clear_supabase_client_lru_cache():
    """lru_cache ignores env changes; reset between tests."""
    _cached_supabase_client.cache_clear()
    yield


SAMPLE_CHUNKS = [
    {
        "text": "Subject: Invoice dispute\nThe payment was due on...",
        "content_hash": "a1b2c3d4e5f67890",
        "source_type": "gmail_thread",
        "source_id": "thread_abc123",
        "source_path": "/path/to/archive.json",
        "metadata": {"subject": "Invoice dispute", "sender": "alice@example.com"},
    },
    {
        "text": "Re: Invoice dispute\nWe acknowledge the delay...",
        "content_hash": "b2c3d4e5f6789012",
        "source_type": "gmail_thread",
        "source_id": "thread_abc123",
        "source_path": "/path/to/archive.json",
        "metadata": {"subject": "Re: Invoice dispute", "sender": "bob@example.com"},
    },
]

SAMPLE_VECTORS = [
    [0.1] * 1536,
    [0.2] * 1536,
]


class TestUpsertChunksWithEmbeddings:
    def test_upsert_empty_chunks(self):
        assert upsert_chunks_with_embeddings([], []) == 0

    def test_upsert_mismatched_lengths(self):
        assert upsert_chunks_with_embeddings(SAMPLE_CHUNKS, [[0.1] * 1536]) == 0

    def test_upsert_none_chunks(self):
        assert upsert_chunks_with_embeddings([], SAMPLE_VECTORS) == 0

    def test_upsert_no_supabase(self):
        with patch.dict(os.environ, {}, clear=True):
            result = upsert_chunks_with_embeddings(SAMPLE_CHUNKS, SAMPLE_VECTORS)
            assert result == 0

    def test_upsert_exception_returns_zero(self):
        mock_cli = MagicMock()
        mock_cli.table.return_value.upsert.return_value.execute.side_effect = (
            RuntimeError("connection refused")
        )
        with patch("src.sal.vector_store.supabase_client", return_value=mock_cli):
            result = upsert_chunks_with_embeddings(SAMPLE_CHUNKS, SAMPLE_VECTORS)
            assert result == 0


class TestSemanticSearch:
    def test_semantic_search_no_supabase(self):
        with patch.dict(os.environ, {}, clear=True):
            result = semantic_search([0.1] * 1536)
            assert result == []

    def test_semantic_search_exception_returns_empty(self):
        mock_cli = MagicMock()
        mock_cli.rpc.return_value.execute.side_effect = RuntimeError("rpc failed")
        with patch("src.sal.vector_store.supabase_client", return_value=mock_cli):
            result = semantic_search([0.1] * 1536, limit=5)
            assert result == []

    def test_semantic_search_with_source_type_filter(self):
        mock_cli = MagicMock()
        mock_result = MagicMock()
        mock_result.data = [{"chunk_text": "hello", "similarity": 0.95}]
        mock_cli.rpc.return_value.execute.return_value = mock_result
        with patch("src.sal.vector_store.supabase_client", return_value=mock_cli):
            result = semantic_search(
                [0.1] * 1536, source_type="gmail_thread", limit=5
            )
            assert result == [{"chunk_text": "hello", "similarity": 0.95}]
            call_args = mock_cli.rpc.call_args
            assert call_args[0][0] == "match_sal_embeddings"
            assert call_args[0][1]["filter_source_type"] == "gmail_thread"


class TestGetEmbeddingStats:
    def test_get_embedding_stats_no_supabase(self):
        with patch.dict(os.environ, {}, clear=True):
            result = get_embedding_stats()
            assert result == {}

    def test_get_embedding_stats_exception_returns_empty(self):
        mock_cli = MagicMock()
        mock_cli.table.return_value.select.return_value.execute.side_effect = (
            RuntimeError("table not found")
        )
        with patch("src.sal.vector_store.supabase_client", return_value=mock_cli):
            result = get_embedding_stats()
            assert result == {}


class TestDeleteSourceEmbeddings:
    def test_delete_source_no_supabase(self):
        with patch.dict(os.environ, {}, clear=True):
            result = delete_source_embeddings("thread_abc123")
            assert result == 0

    def test_delete_exception_returns_zero(self):
        mock_cli = MagicMock()
        mock_cli.table.return_value.delete.return_value.eq.return_value.execute.side_effect = (
            RuntimeError("delete failed")
        )
        with patch("src.sal.vector_store.supabase_client", return_value=mock_cli):
            result = delete_source_embeddings("thread_abc123")
            assert result == 0

    def test_delete_success_returns_count(self):
        mock_cli = MagicMock()
        mock_result = MagicMock()
        mock_result.data = [{"id": 1}, {"id": 2}]
        mock_cli.table.return_value.delete.return_value.eq.return_value.execute.return_value = (
            mock_result
        )
        with patch("src.sal.vector_store.supabase_client", return_value=mock_cli):
            result = delete_source_embeddings("thread_abc123")
            assert result == 2
