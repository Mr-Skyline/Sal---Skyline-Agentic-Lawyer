"""Tests for operator-facing xAI / Grok error hints."""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    InternalServerError,
    RateLimitError,
)

from src.sal.analysis import friendly_sal_api_message


class TestFriendlySalApiMessage(unittest.TestCase):
    def test_empty_choices_runtime(self) -> None:
        msg = friendly_sal_api_message(
            RuntimeError("Grok returned no completion choices (empty response).")
        )
        self.assertIsNotNone(msg)
        self.assertIn("Grok", msg)

    def test_api_connection_error(self) -> None:
        err = APIConnectionError(request=MagicMock())
        msg = friendly_sal_api_message(err)
        self.assertIsNotNone(msg)
        self.assertIn("Connection", msg)

    def test_api_timeout_error(self) -> None:
        err = APITimeoutError(request=MagicMock())
        msg = friendly_sal_api_message(err)
        self.assertIsNotNone(msg)
        self.assertIn("Timeout", msg)

    def test_authentication_error(self) -> None:
        err = AuthenticationError(
            message="bad key", response=MagicMock(), body=None
        )
        msg = friendly_sal_api_message(err)
        self.assertIsNotNone(msg)
        self.assertIn("API key", msg)

    def test_rate_limit_error(self) -> None:
        err = RateLimitError(
            message="slow down", response=MagicMock(), body=None
        )
        msg = friendly_sal_api_message(err)
        self.assertIsNotNone(msg)
        self.assertIn("Rate limit", msg)

    def test_internal_server_error(self) -> None:
        resp = MagicMock()
        resp.status_code = 502
        err = InternalServerError(
            message="upstream", response=resp, body=None
        )
        msg = friendly_sal_api_message(err)
        self.assertIsNotNone(msg)
        self.assertIn("server error", msg.lower())

    def test_chained_cause(self) -> None:
        inner = APIStatusError(
            message="nope",
            response=MagicMock(status_code=401),
            body=None,
        )
        msg = None
        try:
            raise inner
        except APIStatusError as e:
            try:
                raise RuntimeError("wrap") from e
            except RuntimeError as outer:
                msg = friendly_sal_api_message(outer)
        self.assertIsNotNone(msg)
        self.assertIn("401", msg)


if __name__ == "__main__":
    unittest.main()
