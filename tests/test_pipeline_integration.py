"""Integration-level tests for config helpers and pipeline utilities."""
from __future__ import annotations

import unittest

from src.sal.config import normalize_primary_state


class TestNormalizePrimaryState(unittest.TestCase):
    def test_lowercase_converted(self) -> None:
        self.assertEqual(normalize_primary_state("co"), "CO")

    def test_uppercase_passthrough(self) -> None:
        self.assertEqual(normalize_primary_state("FL"), "FL")

    def test_invalid_code_returns_empty(self) -> None:
        self.assertEqual(normalize_primary_state("XX"), "")

    def test_none_returns_empty(self) -> None:
        self.assertEqual(normalize_primary_state(None), "")

    def test_empty_string_returns_empty(self) -> None:
        self.assertEqual(normalize_primary_state(""), "")

    def test_whitespace_stripped(self) -> None:
        self.assertEqual(normalize_primary_state("  AZ  "), "AZ")


if __name__ == "__main__":
    unittest.main()
