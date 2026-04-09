"""Unit tests for src.sal.embeddings — pure functions only (no API calls)."""
from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest

from src.sal.embeddings import (
    _approx_token_count,
    chunk_hash,
    chunk_text,
    chunks_from_thread_archive,
    generate_embeddings,
    load_thread_archive,
)

# ---------------------------------------------------------------------------
# _approx_token_count
# ---------------------------------------------------------------------------

def test_approx_token_count():
    assert _approx_token_count("hello world") >= 1
    assert _approx_token_count("hello world") <= 10


# ---------------------------------------------------------------------------
# chunk_text
# ---------------------------------------------------------------------------

def test_chunk_text_short():
    result = chunk_text("Short text.", max_tokens=500)
    assert result == ["Short text."]


def test_chunk_text_empty():
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_chunk_text_long():
    paragraphs = ["Paragraph number %d. " % i + "Extra detail here." for i in range(40)]
    long = "\n\n".join(paragraphs)
    result = chunk_text(long, max_tokens=50)
    assert len(result) > 1
    for c in result:
        assert len(c) > 0


def test_chunk_text_with_prefix():
    result = chunk_text("Some body text.", max_tokens=500, prefix="Subject: Hello")
    assert len(result) == 1
    assert result[0].startswith("Subject: Hello")


def test_chunk_text_overlap():
    para_a = "Alpha paragraph. " * 60
    para_b = "Beta paragraph. " * 60
    long = para_a.strip() + "\n\n" + para_b.strip()
    result = chunk_text(long, max_tokens=100, overlap_tokens=20)
    assert len(result) >= 2
    tail_of_first = result[0][-40:]
    assert tail_of_first in result[1], "Overlap content should appear in the next chunk"


# ---------------------------------------------------------------------------
# chunk_hash
# ---------------------------------------------------------------------------

def test_chunk_hash():
    h = chunk_hash("hello world")
    assert len(h) == 16
    assert all(c in "0123456789abcdef" for c in h)
    assert chunk_hash("hello world") == h


def test_chunk_hash_different():
    assert chunk_hash("aaa") != chunk_hash("bbb")


# ---------------------------------------------------------------------------
# load_thread_archive
# ---------------------------------------------------------------------------

def test_load_thread_archive_missing_file(tmp_path: Path):
    assert load_thread_archive(tmp_path / "nope.json") == []


def test_load_thread_archive_valid(tmp_path: Path):
    data = [{"thread_id": "t1", "text": "Hello", "subject": "Test"}]
    p = tmp_path / "thread.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    result = load_thread_archive(p)
    assert result == data


def test_load_thread_archive_invalid_json(tmp_path: Path):
    p = tmp_path / "bad.json"
    p.write_text("{not valid json", encoding="utf-8")
    assert load_thread_archive(p) == []


# ---------------------------------------------------------------------------
# chunks_from_thread_archive
# ---------------------------------------------------------------------------

def test_chunks_from_thread_archive(tmp_path: Path):
    messages = [
        {
            "thread_id": "t42",
            "subject": "Contract dispute",
            "sender": "alice@example.com",
            "date": "2026-01-15",
            "message_id": "msg1",
            "text": "This is the first message body.",
        },
        {
            "thread_id": "t42",
            "subject": "Contract dispute",
            "sender": "bob@example.com",
            "date": "2026-01-16",
            "message_id": "msg2",
            "text": "This is the second message body.",
        },
    ]
    p = tmp_path / "archive.json"
    p.write_text(json.dumps(messages), encoding="utf-8")

    result = chunks_from_thread_archive(p)
    assert len(result) >= 2

    required_keys = {"text", "content_hash", "source_type", "source_id", "source_path", "metadata"}
    for chunk in result:
        assert required_keys <= set(chunk.keys())
        assert chunk["source_type"] == "gmail_thread"
        assert chunk["source_id"] == "t42"
        assert "subject" in chunk["metadata"]


def test_chunks_from_thread_archive_empty(tmp_path: Path):
    assert chunks_from_thread_archive(tmp_path / "nonexistent.json") == []


# ---------------------------------------------------------------------------
# generate_embeddings
# ---------------------------------------------------------------------------

def test_generate_embeddings_no_api_key():
    with mock.patch.dict("os.environ", {"EMBEDDING_API_KEY": "", "XAI_API_KEY": ""}, clear=False):
        with pytest.raises(ValueError, match="EMBEDDING_API_KEY"):
            generate_embeddings(["test"], api_key="")


def test_generate_embeddings_empty_list():
    result = generate_embeddings([], api_key="fake-key-for-empty-test")
    assert result == []
