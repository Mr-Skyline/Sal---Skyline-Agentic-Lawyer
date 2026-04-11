"""Tests for src.sal.verify_setup — SetupStatus, run_checks, run_supabase_ping."""
import os
from unittest.mock import patch

from verify_setup import SetupStatus, run_checks, run_supabase_ping

# ---------- SetupStatus namedtuple ----------

def test_setup_status_fields():
    s = SetupStatus(lines=["a", "b"], grok_and_credentials_ok=True, gmail_api_ok=False)
    assert s.lines == ["a", "b"]
    assert s.grok_and_credentials_ok is True
    assert s.gmail_api_ok is False
    assert s._fields == ("lines", "grok_and_credentials_ok", "gmail_api_ok")


# ---------- run_checks ----------

def test_run_checks_returns_setup_status():
    status = run_checks()
    assert isinstance(status, SetupStatus)
    assert isinstance(status.lines, list)
    assert all(isinstance(line, str) for line in status.lines)
    assert isinstance(status.grok_and_credentials_ok, bool)
    assert isinstance(status.gmail_api_ok, bool)


def test_run_checks_no_xai_key():
    env = {k: v for k, v in os.environ.items() if k != "XAI_API_KEY"}
    with patch.dict(os.environ, env, clear=True):
        with patch("verify_setup.load_dotenv"):
            status = run_checks()
    assert status.grok_and_credentials_ok is False


# ---------- run_supabase_ping ----------

def test_supabase_ping_skipped_no_env():
    env = {k: v for k, v in os.environ.items()
           if k not in ("SUPABASE_URL", "SUPABASE_KEY", "SUPABASE_SERVICE_ROLE_KEY")}
    with patch.dict(os.environ, env, clear=True):
        lines, ok = run_supabase_ping()
    assert ok is True
    assert any("skipped" in line.lower() for line in lines)
