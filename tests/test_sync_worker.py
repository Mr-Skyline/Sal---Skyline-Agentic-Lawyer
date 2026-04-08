"""Tests for src.sal.sync_worker — import smoke and CLI argparse."""
import json
import signal
import subprocess
import sys
import threading

import pytest


def test_shutdown_event_is_threading_event():
    from src.sal import sync_worker

    assert isinstance(sync_worker._shutdown, threading.Event)


def test_handle_signal_sets_shutdown_event():
    from src.sal import sync_worker

    sync_worker._shutdown.clear()
    try:
        sync_worker._handle_signal(signal.SIGINT, None)
        assert sync_worker._shutdown.is_set()
    finally:
        sync_worker._shutdown.clear()


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


def test_status_no_health_file_exits_one(tmp_path, monkeypatch):
    """--status with no .health.json exits 1 and prints to stderr."""
    from src.sal import sync_worker as sw

    monkeypatch.setattr(
        sw,
        "default_state_path",
        lambda: tmp_path / "correspondence_sync_state.json",
    )
    monkeypatch.setattr(sys, "argv", ["sync_worker", "--status"])
    with pytest.raises(SystemExit) as exc:
        sw.main()
    assert exc.value.code == 1


def test_write_health_creates_valid_json(tmp_path):
    from src.sal.sync_worker import _write_health

    state_path = tmp_path / "correspondence_sync_state.json"
    summary = {"threads_seen": 4, "archived": 1, "skipped": 2}
    _write_health(state_path, summary, cycle=3)
    health_path = state_path.with_suffix(".health.json")
    assert health_path.exists()
    data = json.loads(health_path.read_text(encoding="utf-8"))
    assert data["cycle"] == 3
    assert data["threads_seen"] == 4
    assert data["archived"] == 1
    assert "last_success" in data


def test_status_prints_health_file_and_exits_zero(tmp_path, monkeypatch, capsys):
    from src.sal import sync_worker as sw

    state_path = tmp_path / "correspondence_sync_state.json"
    health_path = state_path.with_suffix(".health.json")
    payload = {"last_success": "2026-01-01T00:00:00+00:00", "cycle": 1}
    health_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    monkeypatch.setattr(sw, "default_state_path", lambda: state_path)
    monkeypatch.setattr(sys, "argv", ["sync_worker", "--status"])
    with pytest.raises(SystemExit) as exc:
        sw.main()
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "last_success" in out
    assert json.loads(out)["cycle"] == 1
