"""Unit tests for review export naming, config state helpers, and Sal prompt load."""
from __future__ import annotations

import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from src.sal.config import normalize_primary_state, review_state_subdir
from src.sal.review_export import (
    _review_filename,
    default_client_label,
    default_issue_keyword,
)
from src.sal.sal_prompt import load_sal_behavioral_text


class TestReviewExportNaming(unittest.TestCase):
    def test_default_client_label_from_email(self) -> None:
        self.assertEqual(default_client_label("  User@Acme.COM "), "acme")

    def test_default_client_label_no_at(self) -> None:
        self.assertEqual(default_client_label("  solo-label  "), "solo-label")

    def test_default_issue_keyword(self) -> None:
        self.assertEqual(
            default_issue_keyword("Payment dispute\nfor Q1 invoice"),
            "payment_dispute_for_q1_invoice",
        )

    def test_default_issue_keyword_empty(self) -> None:
        self.assertEqual(default_issue_keyword("   \n\t  "), "matter")

    def test_review_filename_fixed_datetime(self) -> None:
        when = datetime(2025, 3, 15, 12, 0, tzinfo=timezone.utc)
        name = _review_filename("Acme Corp", "late pay", when=when)
        self.assertEqual(name, "2025-03-15_acme_corp_late_pay.md")


class TestConfigStateHelpers(unittest.TestCase):
    def test_normalize_primary_state_valid(self) -> None:
        self.assertEqual(normalize_primary_state(" co "), "CO")

    def test_normalize_primary_state_invalid(self) -> None:
        self.assertEqual(normalize_primary_state("XX"), "")

    def test_normalize_primary_state_none(self) -> None:
        self.assertEqual(normalize_primary_state(None), "")

    def test_review_state_subdir_valid(self) -> None:
        self.assertEqual(review_state_subdir("fl"), "FL")

    def test_review_state_subdir_unspecified(self) -> None:
        self.assertEqual(review_state_subdir(""), "_unspecified")
        self.assertEqual(review_state_subdir("bad"), "_unspecified")


class TestSalPromptLoad(unittest.TestCase):
    def test_load_sal_behavioral_text_missing_file(self) -> None:
        with TemporaryDirectory() as td:
            missing = Path(td) / "nope.txt"
            self.assertEqual(load_sal_behavioral_text(sal_path=missing), "")


if __name__ == "__main__":
    unittest.main()
