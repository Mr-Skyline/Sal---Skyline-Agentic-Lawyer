"""Tests for review_export Markdown audit trail helpers."""
import re
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.sal.review_export import (
    _review_filename,
    _slug,
    default_client_label,
    default_issue_keyword,
    export_analysis_markdown,
)


@pytest.fixture
def review_dir(tmp_path):
    with patch("src.sal.review_export.SKYLINE_REVIEW_DIR", tmp_path):
        yield tmp_path


@pytest.fixture(autouse=True)
def no_supabase(monkeypatch):
    monkeypatch.setattr("src.sal.review_export.insert_review_export_meta", lambda **kw: None)


def test_slug_hello_world():
    assert _slug("Hello World!! Test") == "hello_world_test"


def test_slug_empty():
    assert _slug("") == "matter"


def test_slug_truncation():
    assert _slug("A" * 100, max_len=10) == "a" * 10


def test_review_filename_pattern():
    name = _review_filename("acme", "payment")
    assert re.match(r"^\d{4}-\d{2}-\d{2}_acme_payment\.md$", name)


def test_review_filename_fixed_when():
    when = datetime(2024, 6, 15, tzinfo=timezone.utc)
    assert _review_filename("acme", "payment", when=when) == "2024-06-15_acme_payment.md"


def test_default_client_label_from_email():
    assert default_client_label("ceo@skyline-painting.com") == "skyline-painting"


def test_default_client_label_no_domain():
    assert default_client_label("justname") == "justname"


def test_default_issue_keyword_non_empty():
    kw = default_issue_keyword("Unpaid invoice for concrete work in Denver")
    assert kw
    assert re.match(r"^[a-z0-9_]+$", kw)


def test_default_issue_keyword_empty():
    assert default_issue_keyword("") == "matter"


def test_export_analysis_markdown_creates_file(review_dir):
    fixed = datetime(2024, 6, 20, 15, 30, 0, tzinfo=timezone.utc)
    with patch("src.sal.review_export.datetime") as mock_dt:
        mock_dt.now = MagicMock(return_value=fixed)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        path = export_analysis_markdown(
            client_label="acme",
            issue_keyword="payment",
            claim="The client owes us money.",
            assistant_profile="dispute",
            result={
                "analysis": "Strong position on payment terms.",
                "draft_body": "Dear counsel,",
                "citations": ["Smith v. Jones, 123 F.3d 1"],
                "primary_state": "",
            },
            target_email="ceo@example.com",
            evidence_excerpt="Invoice #99",
        )

    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Analysis timestamp" in text
    assert "The client owes us money." in text
    assert "Strong position on payment terms." in text
    assert "Citations" in text
    assert "Smith v. Jones" in text


def test_export_analysis_markdown_appends_on_second_call(review_dir):
    fixed = datetime(2024, 7, 1, 10, 0, 0, tzinfo=timezone.utc)
    with patch("src.sal.review_export.datetime") as mock_dt:
        mock_dt.now = MagicMock(return_value=fixed)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        kwargs = dict(
            client_label="acme",
            issue_keyword="late",
            claim="First intake.",
            assistant_profile="business_counsel",
            result={
                "analysis": "First analysis.",
                "draft_body": "",
                "citations": [],
                "primary_state": "",
            },
            target_email="a@b.com",
        )
        export_analysis_markdown(**kwargs)
        export_analysis_markdown(
            **{
                **kwargs,
                "claim": "Second intake.",
                "result": {
                    "analysis": "Second analysis.",
                    "draft_body": "",
                    "citations": [],
                    "primary_state": "",
                },
            },
        )

    sub = review_dir / "_unspecified"
    files = list(sub.glob("*.md"))
    assert len(files) == 1
    text = files[0].read_text(encoding="utf-8")
    assert "Update" in text


def test_export_analysis_markdown_primary_state_co_subdir(review_dir):
    fixed = datetime(2024, 8, 1, 12, 0, 0, tzinfo=timezone.utc)
    with patch("src.sal.review_export.datetime") as mock_dt:
        mock_dt.now = MagicMock(return_value=fixed)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        path = export_analysis_markdown(
            client_label="x",
            issue_keyword="y",
            claim="c",
            assistant_profile="dispute",
            result={
                "analysis": "a",
                "draft_body": "",
                "citations": [],
                "primary_state": "CO",
            },
            target_email="u@v.com",
        )

    assert path.parent == review_dir / "CO"
    assert path.exists()


def test_export_analysis_markdown_primary_state_empty_unspecified(review_dir):
    fixed = datetime(2024, 9, 1, 12, 0, 0, tzinfo=timezone.utc)
    with patch("src.sal.review_export.datetime") as mock_dt:
        mock_dt.now = MagicMock(return_value=fixed)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        path = export_analysis_markdown(
            client_label="x",
            issue_keyword="y",
            claim="c",
            assistant_profile="dispute",
            result={
                "analysis": "a",
                "draft_body": "",
                "citations": [],
                "primary_state": "",
            },
            target_email="u@v.com",
        )

    assert path.parent == review_dir / "_unspecified"
    assert path.exists()
