"""Unit tests for Sal JSON parsing helpers (no Grok calls)."""
from __future__ import annotations

import unittest

from analysis import _normalize_sal_fields, _parse_sal_response_json


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

    def test_nested_json(self) -> None:
        raw = '{"analysis":"x","draft_body":"","citations":[{"ref":"email","date":"2024-01-01"}],"primary_state":"CO"}'
        data, mode = _parse_sal_response_json(raw)
        self.assertEqual(mode, "direct")
        self.assertEqual(len(data["citations"]), 1)
        self.assertEqual(data["citations"][0]["ref"], "email")

    def test_extracted_nested_json(self) -> None:
        raw = (
            'Here is my analysis:\n'
            '{"analysis":"deep","draft_body":"body","citations":[],'
            '"primary_state":"","metadata":{"model":"grok","tokens":{"in":100,"out":200}}}\n'
            'End.'
        )
        data, mode = _parse_sal_response_json(raw)
        self.assertEqual(mode, "extracted")
        self.assertEqual(data["metadata"]["tokens"]["in"], 100)

    def test_empty_string_raises(self) -> None:
        with self.assertRaises(RuntimeError):
            _parse_sal_response_json("")


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

    def test_normalize_missing_all_fields(self) -> None:
        d: dict = {}
        _normalize_sal_fields(d)
        self.assertEqual(d["draft_body"], "")
        self.assertEqual(d["analysis"], "")
        self.assertEqual(d["citations"], [])


if __name__ == "__main__":
    unittest.main()
