"""Tests for gmail_retry, logger_util, and secrets_store utility modules."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import httplib2
from googleapiclient.errors import HttpError

from gmail_retry import gmail_execute
from logger_util import log_event
from secrets_store import (
    _valid_google_oauth_client,
    save_api_keys_to_dotenv,
    save_gmail_credentials_json,
)


def _make_http_error(status: int) -> HttpError:
    resp = httplib2.Response({"status": status})
    return HttpError(resp, b"error")


# ========== gmail_retry ==========

class TestGmailExecute:
    def test_success_returns_result(self):
        req = MagicMock()
        req.execute.return_value = {"id": "msg_1"}
        assert gmail_execute(req) == {"id": "msg_1"}
        req.execute.assert_called_once()

    @patch("gmail_retry.time.sleep")
    def test_retry_on_429_then_succeed(self, mock_sleep):
        req = MagicMock()
        req.execute.side_effect = [
            _make_http_error(429),
            {"id": "msg_ok"},
        ]
        result = gmail_execute(req, max_retries=3)
        assert result == {"id": "msg_ok"}
        assert req.execute.call_count == 2
        mock_sleep.assert_called_once()

    def test_non_retryable_raises_immediately(self):
        req = MagicMock()
        req.execute.side_effect = _make_http_error(404)
        try:
            gmail_execute(req)
            assert False, "Should have raised HttpError"
        except HttpError as e:
            assert e.resp.status == 404
        assert req.execute.call_count == 1

    def test_non_retryable_403(self):
        req = MagicMock()
        req.execute.side_effect = _make_http_error(403)
        try:
            gmail_execute(req)
            assert False, "Should have raised"
        except HttpError as e:
            assert e.resp.status == 403

    @patch("gmail_retry.time.sleep")
    def test_retry_on_500(self, mock_sleep):
        req = MagicMock()
        req.execute.side_effect = [
            _make_http_error(500),
            _make_http_error(502),
            {"ok": True},
        ]
        result = gmail_execute(req, max_retries=5)
        assert result == {"ok": True}
        assert req.execute.call_count == 3

    @patch("gmail_retry.time.sleep")
    def test_exhausted_retries_raises(self, mock_sleep):
        req = MagicMock()
        req.execute.side_effect = _make_http_error(429)
        try:
            gmail_execute(req, max_retries=2)
            assert False, "Should have raised"
        except HttpError:
            pass
        assert req.execute.call_count == 2


# ========== logger_util ==========

class TestLogEvent:
    def test_writes_jsonl(self):
        with tempfile.NamedTemporaryFile(
            suffix=".jsonl", delete=False, mode="w"
        ) as f:
            log_path = f.name
        try:
            with patch("logger_util.LOG_FILE", log_path):
                log_event("test_event", extra={"key": "val"})
            with open(log_path, encoding="utf-8") as f:
                line = f.readline()
            row = json.loads(line)
            assert row["event"] == "test_event"
            assert row["extra"] == {"key": "val"}
            assert "ts" in row
        finally:
            os.unlink(log_path)

    def test_error_field(self):
        with tempfile.NamedTemporaryFile(
            suffix=".jsonl", delete=False, mode="w"
        ) as f:
            log_path = f.name
        try:
            with patch("logger_util.LOG_FILE", log_path):
                log_event("fail_event", error="something broke")
            with open(log_path, encoding="utf-8") as f:
                row = json.loads(f.readline())
            assert row["error"] == "something broke"
        finally:
            os.unlink(log_path)

    def test_no_crash_on_bad_path(self):
        with patch("logger_util.LOG_FILE", "/nonexistent_dir/log.jsonl"):
            log_event("should_not_crash")


# ========== secrets_store ==========

class TestValidGoogleOauthClient:
    def test_valid_installed(self):
        data = {"installed": {"client_id": "x", "client_secret": "y"}}
        assert _valid_google_oauth_client(data) is True

    def test_valid_web(self):
        data = {"web": {"client_id": "abc", "client_secret": "def"}}
        assert _valid_google_oauth_client(data) is True

    def test_empty_dict(self):
        assert _valid_google_oauth_client({}) is False

    def test_missing_secret(self):
        data = {"installed": {"client_id": "x"}}
        assert _valid_google_oauth_client(data) is False

    def test_missing_id(self):
        data = {"installed": {"client_secret": "y"}}
        assert _valid_google_oauth_client(data) is False

    def test_wrong_key(self):
        data = {"other": {"client_id": "x", "client_secret": "y"}}
        assert _valid_google_oauth_client(data) is False


class TestSaveApiKeysToDotenv:
    def test_creates_env_with_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            written = save_api_keys_to_dotenv(root, xai_api_key="test-key-123")
            assert "XAI_API_KEY" in written
            env_path = root / ".env"
            assert env_path.exists()
            content = env_path.read_text()
            assert "XAI_API_KEY=test-key-123" in content

    def test_skips_empty_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            written = save_api_keys_to_dotenv(root, xai_api_key="", zhipu_api_key="")
            assert written == []

    def test_both_keys(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            written = save_api_keys_to_dotenv(
                root, xai_api_key="xai_val", zhipu_api_key="zhipu_val"
            )
            assert "XAI_API_KEY" in written
            assert "ZHIPU_API_KEY" in written
            content = (root / ".env").read_text()
            assert "xai_val" in content
            assert "zhipu_val" in content


class TestSaveGmailCredentialsJson:
    def test_valid_json_saved(self):
        data = {"installed": {"client_id": "cid", "client_secret": "csec"}}
        raw = json.dumps(data).encode("utf-8")
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            save_gmail_credentials_json(root, raw)
            dest = root / "credentials.json"
            assert dest.exists()
            loaded = json.loads(dest.read_text())
            assert loaded == data

    def test_invalid_json_raises(self):
        try:
            save_gmail_credentials_json(Path("/tmp"), b"not json {{{")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "JSON" in str(e)

    def test_missing_oauth_block_raises(self):
        data = {"something_else": {"client_id": "x"}}
        raw = json.dumps(data).encode("utf-8")
        try:
            save_gmail_credentials_json(Path("/tmp"), raw)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "client_id" in str(e) or "OAuth" in str(e)
