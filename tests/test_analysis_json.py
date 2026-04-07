"""Unit tests for Sal JSON parsing helpers (no Grok calls)."""
from __future__ import annotations

import unittest

from src.sal.analysis import _normalize_sal_fields, _parse_sal_response_json


class TestParseSalResponseJson(unittest.TestCase):
    def test_direct_object(self) -> None:
        raw = '{"analysis":"a","draft_body":"","citations":[],"primary_state":""}'
        data, mode = _parse_sal_response_json(raw)
        self.assertEqual(mode, "direct")
        self.assertEqual(data["analysis"], "a")

    def test_extracted_after_prose(self) -> None:
        raw = (
            "Here you go:\n"
            '{"analysis":"x","draft_body":"","citations":[],"primary_state":""}\n'
        )
        data, mode = _parse_sal_response_json(raw)
        self.assertEqual(mode, "extracted")
        self.assertEqual(data["analysis"], "x")

    def test_strips_json_code_fence(self) -> None:
        raw = (
            "```json\n"
            '{"analysis":"","draft_body":"hi","citations":[],"primary_state":""}\n'
            "```"
        )
        data, mode = _parse_sal_response_json(raw)
        self.assertEqual(data["draft_body"], "hi")
        self.assertEqual(mode, "direct")

    def test_bom_strip(self) -> None:
        raw = (
            "\ufeff"
            '{"analysis":"","draft_body":"","citations":[],"primary_state":""}'
        )
        data, mode = _parse_sal_response_json(raw)
        self.assertEqual(mode, "direct")
        self.assertIn("analysis", data)

    def test_array_top_level_raises(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            _parse_sal_response_json("[1,2,3]")
        self.assertIn("object", str(ctx.exception).lower())


class TestNormalizeSalFields(unittest.TestCase):
    def test_citations_string_to_list(self) -> None:
        d: dict = {"citations": "single ref", "analysis": None, "draft_body": None}
        _normalize_sal_fields(d)
        self.assertEqual(d["citations"], ["single ref"])
        self.assertEqual(d["analysis"], "")
        self.assertEqual(d["draft_body"], "")

    def test_reply_alias(self) -> None:
        d: dict = {"reply": "body text"}
        _normalize_sal_fields(d)
        self.assertEqual(d["draft_body"], "body text")


if __name__ == "__main__":
    unittest.main()
