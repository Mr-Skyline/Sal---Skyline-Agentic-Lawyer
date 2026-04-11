"""Tests for src.sal.ingest — sync state, query builder, and default paths."""
import json
from pathlib import Path

from ingest import (
    cc_monitor_gmail_query,
    default_state_path,
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
