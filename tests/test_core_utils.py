"""Tests for config, review_export, and sal_prompt core utilities."""
from pathlib import Path

from sal.config import normalize_primary_state, review_state_subdir
from review_export import default_client_label, default_issue_keyword
from sal_prompt import (
    default_sal_prompt_path,
    json_tool_contract_suffix,
    load_sal_behavioral_text,
    run_mode_suffix,
)

# ---------- config: normalize_primary_state ----------

def test_normalize_valid_states():
    assert normalize_primary_state("CO") == "CO"
    assert normalize_primary_state("co") == "CO"
    assert normalize_primary_state("FL") == "FL"
    assert normalize_primary_state("AZ") == "AZ"
    assert normalize_primary_state("TX") == "TX"
    assert normalize_primary_state("NE") == "NE"


def test_normalize_invalid_states():
    assert normalize_primary_state("XX") == ""
    assert normalize_primary_state("California") == ""
    assert normalize_primary_state(None) == ""
    assert normalize_primary_state("") == ""
    assert normalize_primary_state(42) == ""


# ---------- config: review_state_subdir ----------

def test_review_state_subdir_valid():
    assert review_state_subdir("CO") == "CO"
    assert review_state_subdir("fl") == "FL"


def test_review_state_subdir_invalid():
    assert review_state_subdir("") == "_unspecified"
    assert review_state_subdir("XX") == "_unspecified"
    assert review_state_subdir(None) == "_unspecified"


# ---------- review_export: default_client_label ----------

def test_default_client_label_email():
    assert default_client_label("john@acme.com") == "acme"
    assert default_client_label("info@skyline-painting.com") == "skyline-painting"


def test_default_client_label_plain():
    assert default_client_label("justtext") == "justtext"


# ---------- review_export: default_issue_keyword ----------

def test_default_issue_keyword():
    result = default_issue_keyword("Payment dispute over unpaid invoice for concrete work")
    assert len(result) > 0
    assert "_" in result or result.isalpha()


def test_default_issue_keyword_empty():
    assert default_issue_keyword("") == "matter"
    assert default_issue_keyword("   ") == "matter"


# ---------- sal_prompt ----------

def test_load_missing_file():
    result = load_sal_behavioral_text(sal_path=Path("/nonexistent/path/to/file.txt"))
    assert result == ""


def test_default_sal_prompt_path_returns_path():
    p = default_sal_prompt_path()
    assert isinstance(p, Path)


def test_json_tool_contract_suffix():
    result = json_tool_contract_suffix(state_codes_csv="CO, FL, AZ")
    assert "JSON" in result
    assert "CO, FL, AZ" in result
    assert "primary_state" in result


def test_run_mode_suffix_dispute():
    result = run_mode_suffix(assistant_profile="dispute")
    assert "dispute" in result.lower()


def test_run_mode_suffix_business():
    result = run_mode_suffix(assistant_profile="business_counsel")
    assert "business" in result.lower() or "commercial" in result.lower()
