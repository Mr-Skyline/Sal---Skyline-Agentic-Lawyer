"""Tests for src.sal.ingest — sync state, query builder, and default paths."""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.sal.ingest import (
    cc_monitor_gmail_query,
    default_state_path,
    fetch_thread_evidence,
    format_sync_summary,
    load_sync_state,
    save_sync_state,
)

# ---------- cc_monitor_gmail_query ----------

def test_cc_monitor_query_default_days():
    q = cc_monitor_gmail_query("agent@test.com")
    assert "cc:agent@test.com" in q
    assert "to:agent@test.com" in q
    assert "newer_than:" in q
    assert q.endswith("d")


def test_cc_monitor_query_custom_days():
    q = cc_monitor_gmail_query("agent@test.com", newer_than_days=30)
    assert "newer_than:30d" in q
    assert "cc:agent@test.com" in q
    assert "to:agent@test.com" in q


def test_cc_monitor_query_one_day():
    q = cc_monitor_gmail_query("me@example.org", newer_than_days=1)
    assert "newer_than:1d" in q


# ---------- load_sync_state ----------

def test_load_sync_state_nonexistent():
    result = load_sync_state(Path("/nonexistent/path/state.json"))
    assert result == {"threads": {}}


def test_load_sync_state_valid_json(tmp_path):
    state_file = tmp_path / "state.json"
    data = {"threads": {"abc123": 1700000000000}, "extra": True}
    state_file.write_text(json.dumps(data), encoding="utf-8")
    result = load_sync_state(state_file)
    assert result == data
    assert result["threads"]["abc123"] == 1700000000000


def test_load_sync_state_corrupt_json(tmp_path):
    state_file = tmp_path / "state.json"
    state_file.write_text("{bad json???", encoding="utf-8")
    result = load_sync_state(state_file)
    assert result == {"threads": {}}


# ---------- save_sync_state ----------

def test_save_then_load_roundtrip(tmp_path):
    state_file = tmp_path / "sub" / "state.json"
    data = {"threads": {"t1": 111, "t2": 222}, "meta": "hello"}
    save_sync_state(state_file, data)
    assert state_file.exists()

    raw = json.loads(state_file.read_text(encoding="utf-8"))
    assert raw == data

    loaded = load_sync_state(state_file)
    assert loaded == data


def test_save_sync_state_creates_parent_dirs(tmp_path):
    deep = tmp_path / "a" / "b" / "c" / "state.json"
    save_sync_state(deep, {"threads": {}})
    assert deep.exists()


# ---------- default_state_path ----------

def test_default_state_path():
    p = default_state_path()
    assert isinstance(p, Path)
    assert p.name == "correspondence_sync_state.json"


# ---------- format_sync_summary ----------


def test_format_sync_summary_keys_and_human_summary():
    summary = {"query": "q", "threads_seen": 5, "archived": 2, "skipped": 3}
    out = format_sync_summary(summary, "agent@example.com", cycle_number=7)
    assert out["agent_email"] == "agent@example.com"
    assert out["cycle"] == 7
    assert out["status"] == "ok"
    assert out["threads_seen"] == 5
    assert out["archived"] == 2
    assert out["skipped"] == 3
    assert out["human_summary"] == (
        "Cycle 7: 5 threads seen, 2 archived, 3 unchanged"
    )


def test_format_sync_summary_zero_values():
    summary = {"query": "q", "threads_seen": 0, "archived": 0, "skipped": 0}
    out = format_sync_summary(summary, "a@b.co", cycle_number=0)
    assert out["status"] == "ok"
    assert out["human_summary"] == (
        "Cycle 0: 0 threads seen, 0 archived, 0 unchanged"
    )


# ---------- fetch_thread_evidence ----------


def test_fetch_thread_evidence_delegates_to_fetch_messages():
    svc = MagicMock()
    fake_items = [{"source": "gmail", "message_id": "m1", "text": "hi"}]
    with patch("src.sal.ingest.fetch_messages_for_evidence") as mock_fetch:
        mock_fetch.return_value = (fake_items, "thread:t1")
        items, desc = fetch_thread_evidence(svc, "t1", max_messages=42)
        mock_fetch.assert_called_once_with(
            svc, "me", "", thread_id="t1", max_messages=42
        )
        assert items == fake_items
        assert desc == "thread:t1"
