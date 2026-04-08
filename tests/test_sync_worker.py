"""Tests for src.sal.sync_worker — import smoke and CLI argparse."""
import subprocess
import sys


def test_import_sync_worker():
    """Module imports without error."""
    from src.sal.sync_worker import main  # noqa: F401
    assert callable(main)


def test_sync_worker_help_exits_zero():
    """--help prints usage and exits 0 (argparse is wired correctly)."""
    result = subprocess.run(
        [sys.executable, "-m", "src.sal.sync_worker", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    assert "sync" in result.stdout.lower() or "gmail" in result.stdout.lower()


def test_sync_worker_no_agent_email_exits_one():
    """Without AGENT_GMAIL_ADDRESS the worker exits with code 1."""
    import os
    env = {k: v for k, v in os.environ.items() if k != "AGENT_GMAIL_ADDRESS"}
    env["AGENT_GMAIL_ADDRESS"] = ""
    result = subprocess.run(
        [sys.executable, "-m", "src.sal.sync_worker", "--once"],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )
    assert result.returncode == 1
    assert "AGENT_GMAIL_ADDRESS" in result.stderr
