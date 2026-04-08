"""
Load Sal behavioral system text from the Skyline prompt file (excludes Phase 8 roadmap).

See DOCUMENT MAP at top of `Skyline Lawyer – Full System Prompt.txt`.
"""
from __future__ import annotations

import os
from pathlib import Path

from .config import ROOT

_DEFAULT_FILENAME = os.path.join("prompts", "Skyline Lawyer – Full System Prompt.txt")
_PHASE8_MARKER = "**Phase 8"
_SAL_ANCHOR = "**Sal —"


def default_sal_prompt_path() -> Path:
    raw = os.environ.get("SAL_PROMPT_PATH", "").strip()
    if raw:
        return Path(os.path.expandvars(os.path.expanduser(raw))).resolve()
    return (ROOT / _DEFAULT_FILENAME).resolve()


def load_sal_behavioral_text(*, sal_path: Path | None = None) -> str:
    """
    Return Sal behavioral sections through Phase 7 + hard rules; drop DOCUMENT MAP
    and everything from Phase 8 onward.
    """
    path = sal_path or default_sal_prompt_path()
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    if _PHASE8_MARKER in text:
        text = text.split(_PHASE8_MARKER, 1)[0]
    text = text.rstrip()
    if _SAL_ANCHOR in text:
        text = text[text.index(_SAL_ANCHOR) :]
    return text.strip()


def json_tool_contract_suffix(*, state_codes_csv: str) -> str:
    """Instructions appended so Grok returns the API shape Streamlit expects."""
    return (
        "\n\n---\nTOOL JSON OUTPUT CONTRACT (Streamlit / Grok API):\n"
        "Respond with a single JSON object only (no markdown fences). Required keys: "
        '"analysis" (string), "draft_body" (string), "citations" (array of strings), '
        f'"primary_state" (string). primary_state must be one of {state_codes_csv} when '
        "the governing project state is clear from evidence or user instruction; otherwise "
        'use an empty string. This value is for file routing only—not a legal determination. '
        "Fold your structured reasoning into analysis; put the email body in draft_body."
    )


def run_mode_suffix(*, assistant_profile: str) -> str:
    if assistant_profile == "business_counsel":
        return (
            "\n\nRUN MODE (business counsel): Keep draft_body professional and commercial; "
            "collaborative when appropriate, direct when necessary."
        )
    return (
        "\n\nRUN MODE (dispute): Cross-check evidence against the user's claim; draft_body "
        "should be thread-safe, polite, and firm."
    )
