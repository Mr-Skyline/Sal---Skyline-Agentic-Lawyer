"""Tests for embed_jobs — chunking and loading (no API calls)."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from embed_jobs import chunk_text, load_review_chunks, load_thread_chunks


class TestChunkText:
    def test_short_text_single_chunk(self):
        result = chunk_text("Hello world", max_tokens=100)
        assert result == ["Hello world"]

    def test_long_text_multiple_chunks(self):
        text = "A" * 4000
        result = chunk_text(text, max_tokens=512, overlap=64)
        assert len(result) > 1
        assert all(len(c) <= 512 * 4 for c in result)

    def test_empty_text(self):
        result = chunk_text("")
        assert result == []

    def test_overlap_present(self):
        text = "A" * 4000
        chunks = chunk_text(text, max_tokens=512, overlap=64)
        if len(chunks) >= 2:
            end_of_first = chunks[0][-256:]
            start_of_second = chunks[1][:256]
            assert end_of_first == start_of_second


class TestLoadThreadChunks:
    def test_loads_from_archive(self):
        with tempfile.TemporaryDirectory() as d:
            thread = {
                "thread_id": "abc123",
                "subject": "Test thread",
                "messages": [{"body": "This is the body of a test email."}],
            }
            Path(d, "abc123.json").write_text(json.dumps(thread), encoding="utf-8")
            chunks = load_thread_chunks(d)
            assert len(chunks) >= 1
            assert chunks[0]["source_type"] == "thread"
            assert chunks[0]["source_id"] == "abc123"
            assert "Test thread" in chunks[0]["content"]

    def test_skips_bad_json(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "bad.json").write_text("not json", encoding="utf-8")
            chunks = load_thread_chunks(d)
            assert chunks == []

    def test_missing_dir(self):
        chunks = load_thread_chunks("/nonexistent/path")
        assert chunks == []


class TestLoadReviewChunks:
    def test_loads_markdown(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "CO").mkdir()
            (p / "CO" / "test.md").write_text(
                "# Title\n\nSome content\n\n## Section 2\n\nMore content",
                encoding="utf-8",
            )
            chunks = load_review_chunks(p)
            assert len(chunks) >= 1
            assert chunks[0]["source_type"] == "review"

    def test_empty_dir(self):
        with tempfile.TemporaryDirectory() as d:
            chunks = load_review_chunks(Path(d))
            assert chunks == []
