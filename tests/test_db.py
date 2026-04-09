"""Tests for src.sal.db — Supabase persistence layer (no live Supabase)."""
from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from src.sal.db import (
    _cached_supabase_client,
    batch_upsert_correspondence_threads,
    get_correspondence_thread,
    insert_review_export_meta,
    list_review_exports,
    supabase_client,
    upsert_correspondence_thread,
)


@pytest.fixture(autouse=True)
def _clear_supabase_client_lru_cache():
    """lru_cache ignores env changes; reset between tests."""
    _cached_supabase_client.cache_clear()
    yield


class TestSupabaseClient:
    def test_no_env_vars_returns_none(self):
        with patch.dict(os.environ, {}, clear=True):
            assert supabase_client() is None

    def test_url_only_returns_none(self):
        with patch.dict(os.environ, {"SUPABASE_URL": "https://example.supabase.co"}, clear=True):
            assert supabase_client() is None

    def test_key_only_returns_none(self):
        with patch.dict(os.environ, {"SUPABASE_SERVICE_ROLE_KEY": "some_key"}, clear=True):
            assert supabase_client() is None

    def test_whitespace_values_returns_none(self):
        with patch.dict(
            os.environ,
            {"SUPABASE_URL": "  ", "SUPABASE_SERVICE_ROLE_KEY": "  "},
            clear=True,
        ):
            assert supabase_client() is None

    def test_cached_client_returns_none_no_env(self):
        _cached_supabase_client.cache_clear()
        with patch.dict(os.environ, {}, clear=True):
            assert _cached_supabase_client() is None


class TestBatchUpsertCorrespondenceThreads:
    def test_batch_upsert_no_supabase(self):
        with patch.dict(os.environ, {}, clear=True):
            n = batch_upsert_correspondence_threads(
                [{"gmail_thread_id": "t1", "subject": "a"}]
            )
            assert n == 0

    def test_batch_upsert_empty_list(self):
        assert batch_upsert_correspondence_threads([]) == 0


class TestGetCorrespondenceThread:
    def test_get_thread_no_supabase(self):
        with patch.dict(os.environ, {}, clear=True):
            assert get_correspondence_thread("abc") is None


class TestListReviewExports:
    def test_list_exports_no_supabase(self):
        with patch.dict(os.environ, {}, clear=True):
            assert list_review_exports() == []

    def test_list_exports_with_state_filter_no_supabase(self):
        with patch.dict(os.environ, {}, clear=True):
            assert list_review_exports(primary_state="CO") == []


class TestUpsertCorrespondenceThread:
    def test_noop_when_no_supabase(self):
        with patch("src.sal.db.supabase_client", return_value=None):
            upsert_correspondence_thread({"gmail_thread_id": "t123", "subject": "test"})

    def test_exception_in_upsert_is_caught(self):
        mock_cli = _mock_supabase_client_raising(RuntimeError("connection refused"))
        with patch("src.sal.db.supabase_client", return_value=mock_cli):
            upsert_correspondence_thread({"gmail_thread_id": "t456"})


class TestInsertReviewExportMeta:
    def test_noop_when_no_supabase(self):
        with patch("src.sal.db.supabase_client", return_value=None):
            insert_review_export_meta(
                primary_state="CO",
                state_subdir="CO",
                file_name="review_2026.md",
            )

    def test_exception_in_insert_is_caught(self):
        mock_cli = _mock_supabase_client_raising(RuntimeError("schema missing"))
        with patch("src.sal.db.supabase_client", return_value=mock_cli):
            insert_review_export_meta(
                primary_state=None,
                state_subdir="_unspecified",
                file_name="test.md",
            )


def _mock_supabase_client_raising(exc: Exception):
    """Return a mock Supabase client whose table().upsert/insert().execute() raises."""
    from unittest.mock import MagicMock

    cli = MagicMock()
    table = MagicMock()
    table.upsert.return_value.execute.side_effect = exc
    table.insert.return_value.execute.side_effect = exc
    cli.table.return_value = table
    return cli
