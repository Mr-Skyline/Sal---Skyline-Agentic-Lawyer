"""Tests for src.sal.db — Supabase persistence layer (no live Supabase)."""
from __future__ import annotations

import os
from unittest.mock import patch

from src.sal.db import insert_review_export_meta, supabase_client, upsert_correspondence_thread


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
