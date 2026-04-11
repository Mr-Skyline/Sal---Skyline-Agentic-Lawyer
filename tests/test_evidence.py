"""Tests for src.sal.evidence — pure/local functions only (no Gmail API)."""
from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import MagicMock

from evidence import (
    claim_to_query_keywords,
    merge_evidence_json,
    parse_document_files,
    parse_pasted_texts,
    partition_evidence_upload_paths,
    save_uploaded_files,
)

# ---------- claim_to_query_keywords ----------

class TestClaimToQueryKeywords:
    def test_basic_claim(self):
        result = claim_to_query_keywords("Payment dispute over unpaid concrete work")
        words = result.split()
        assert len(words) <= 6
        assert all(len(w) > 1 for w in words)
        fn_stop = {
            "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "as", "is", "was", "are", "were", "be", "been", "being", "have",
            "has", "had", "do", "does", "did", "will", "would", "could", "should",
            "i", "you", "he", "she", "it", "we", "they", "me", "my", "not", "no",
        }
        assert all(w not in fn_stop for w in words)

    def test_empty_string(self):
        assert claim_to_query_keywords("") == ""

    def test_whitespace_only(self):
        assert claim_to_query_keywords("   ") == ""

    def test_max_six_words(self):
        result = claim_to_query_keywords(
            "contractor failed payment invoice concrete masonry driveway foundation roofing"
        )
        assert len(result.split()) <= 6

    def test_stop_words_removed(self):
        result = claim_to_query_keywords("I have a payment for the work")
        words = result.split()
        assert "i" not in words
        assert "have" not in words
        assert "a" not in words
        assert "the" not in words
        assert "for" not in words
        assert "payment" in words
        assert "work" in words


# ---------- parse_pasted_texts ----------

class TestParsePastedTexts:
    def test_empty_string(self):
        assert parse_pasted_texts("") == []

    def test_whitespace_only(self):
        assert parse_pasted_texts("   \n  ") == []

    def test_plain_line(self):
        rows = parse_pasted_texts("just a plain line")
        assert len(rows) == 1
        assert rows[0]["source"] == "pasted"
        assert rows[0]["text"] == "just a plain line"

    def test_dated_from_format(self):
        rows = parse_pasted_texts("1/15/2024 From: John - Payment is late")
        assert len(rows) == 1
        r = rows[0]
        assert r["source"] == "pasted"
        assert r["date"] == "1/15/2024"
        assert "Payment is late" in r["text"]

    def test_multiple_lines(self):
        text = "1/15/2024 From: John - Payment is late\njust a note\n2024-01-20 [From] Jane: Got your message"
        rows = parse_pasted_texts(text)
        assert len(rows) == 3
        assert rows[0]["date"] == "1/15/2024"
        assert rows[1]["text"] == "just a note"
        assert rows[2]["date"] == "2024-01-20"

    def test_bracket_date_format(self):
        rows = parse_pasted_texts("[Jan 5] Alice: See you tomorrow")
        assert len(rows) == 1
        assert rows[0]["date"] == "Jan 5"


# ---------- merge_evidence_json ----------

class TestMergeEvidenceJson:
    def test_single_item(self):
        items = [{"source": "gmail", "text": "hi"}]
        result = merge_evidence_json(items)
        parsed = json.loads(result)
        assert parsed == items

    def test_empty_list(self):
        result = merge_evidence_json([])
        assert json.loads(result) == []

    def test_unicode_preserved(self):
        items = [{"text": "caf\u00e9 \u2014 payment"}]
        result = merge_evidence_json(items)
        assert "caf\u00e9" in result


# ---------- partition_evidence_upload_paths ----------

class TestPartitionEvidenceUploadPaths:
    def test_standard_partition(self):
        ocr, docs = partition_evidence_upload_paths(
            ["photo.png", "doc.txt", "scan.pdf", "notes.md"]
        )
        assert "photo.png" in ocr
        assert "scan.pdf" in ocr
        assert "doc.txt" in docs
        assert "notes.md" in docs

    def test_empty_list(self):
        assert partition_evidence_upload_paths([]) == ([], [])

    def test_unknown_extension_ignored(self):
        ocr, docs = partition_evidence_upload_paths(["archive.zip", "data.csv"])
        assert ocr == []
        assert docs == []

    def test_all_image_types(self):
        ocr, docs = partition_evidence_upload_paths(
            ["a.png", "b.jpg", "c.jpeg", "d.webp", "e.gif"]
        )
        assert len(ocr) == 5
        assert len(docs) == 0


# ---------- parse_document_files ----------

class TestParseDocumentFiles:
    def test_real_txt_file(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("This is test evidence content.")
            f.flush()
            path = f.name
        try:
            rows = parse_document_files([path])
            assert len(rows) == 1
            assert rows[0]["source"] == "document"
            assert "test evidence content" in rows[0]["text"]
            assert rows[0]["proof"].startswith("upload:")
        finally:
            os.unlink(path)

    def test_real_md_file(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write("# Evidence\nPayment record attached.")
            f.flush()
            path = f.name
        try:
            rows = parse_document_files([path])
            assert len(rows) == 1
            assert "Payment record" in rows[0]["text"]
        finally:
            os.unlink(path)

    def test_nonexistent_file(self):
        rows = parse_document_files(["/tmp/nonexistent_file_abc123.txt"])
        assert rows == []

    def test_empty_txt_file(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("")
            f.flush()
            path = f.name
        try:
            rows = parse_document_files([path])
            assert rows == []
        finally:
            os.unlink(path)


# ---------- save_uploaded_files ----------

class TestSaveUploadedFiles:
    def test_mock_uploaded_file(self):
        mock_file = MagicMock()
        mock_file.name = "evidence_photo.png"
        mock_file.getbuffer.return_value = b"\x89PNG\r\n\x1a\n fake image data"
        paths = save_uploaded_files([mock_file])
        assert len(paths) == 1
        assert paths[0].endswith("evidence_photo.png")
        assert os.path.isfile(paths[0])
        with open(paths[0], "rb") as f:
            assert f.read() == b"\x89PNG\r\n\x1a\n fake image data"

    def test_empty_upload_list(self):
        assert save_uploaded_files([]) == []

    def test_none_upload(self):
        assert save_uploaded_files(None) == []
