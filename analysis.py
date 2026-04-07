"""
Grok (xAI) analysis + draft generation with exponential backoff retries.
"""
from __future__ import annotations

import json
import os
import random
import re
import time
from functools import lru_cache
from typing import Any, Dict, Optional

from config import (
    API_BASE_DELAY_SEC,
    API_MAX_RETRIES,
    GROK_BASE_URL,
    GROK_MODEL,
    JOB_SITE_STATE_CODES,
    normalize_primary_state,
)
from logger_util import log_event
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    InternalServerError,
    OpenAI,
    RateLimitError,
)

from sal_prompt import (
    json_tool_contract_suffix,
    load_sal_behavioral_text,
    run_mode_suffix,
)

_STATE_CODES_S = ", ".join(JOB_SITE_STATE_CODES)

SYSTEM_PROMPT_DISPUTE = (
    "You are an elite dispute communications assistant (not a lawyer): cross-check evidence "
    "against the user's claim, identify contradictions or gaps, and draft a thread-safe email "
    "reply that is polite but firm. Cite sources exactly (e.g. dates, Gmail snippets, "
    "screenshot filenames). Do not state legal conclusions or guaranteed outcomes. "
    "Infer from the evidence and summary where the project or dispute primarily sits geographically "
    f"(US state). Output a single JSON object with keys: analysis (string), draft_body (string), "
    "citations (array of strings), primary_state (string). "
    f"primary_state must be exactly one of {_STATE_CODES_S} when the location is clear from context; "
    "otherwise use an empty string. This value is only used to separate stored records by state—not a "
    "legal determination. No markdown fences, only valid JSON."
)

SYSTEM_PROMPT_BUSINESS = (
    "You are an elite business counsel communications assistant (not a lawyer): review the "
    "evidence and the user's summary. Identify material risks, ambiguities, and practical "
    "next steps. Draft clear, professional email language suitable for commercial "
    "correspondence — collaborative when appropriate, direct when necessary. "
    "Do not give legal advice or guarantee outcomes. "
    "Infer from the evidence and summary where the project or dispute primarily sits geographically "
    f"(US state). Output a single JSON object with keys: analysis (string), draft_body (string), "
    "citations (array of strings), primary_state (string). "
    f"primary_state must be exactly one of {_STATE_CODES_S} when the location is clear from context; "
    "otherwise use an empty string. This value is only used to separate stored records by state—not a "
    "legal determination. No markdown fences, only valid JSON."
)


def _parse_sal_response_json(raw: str) -> tuple[Dict[str, Any], str]:
    """Parse Grok JSON output; return (data, mode). Mode is direct vs extracted from prose."""
    text = raw.strip()
    if text.startswith("\ufeff"):
        text = text[1:]
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```\s*$", "", text)
    text = text.strip()
    first = text.find("{")
    last = text.rfind("}")
    if first == -1 or last == -1 or last <= first:
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as e:
            raise RuntimeError("No JSON object found in Grok response") from e
        if isinstance(parsed, list):
            raise RuntimeError("Expected JSON object, got array")
        if not isinstance(parsed, dict):
            raise RuntimeError("Expected JSON object")
        return parsed, "direct"
    try:
        data = json.loads(text[first : last + 1])
    except json.JSONDecodeError as e:
        raise RuntimeError("No JSON object found in Grok response") from e
    if isinstance(data, list):
        raise RuntimeError("Expected JSON object, got array")
    if not isinstance(data, dict):
        raise RuntimeError("Expected JSON object")
    mode = "extracted" if first > 0 else "direct"
    return data, mode


def _normalize_sal_fields(d: Dict[str, Any]) -> None:
    """Normalize Sal JSON fields in place."""
    cit = d.get("citations")
    if isinstance(cit, str):
        d["citations"] = [cit]
    if d.get("analysis") is None:
        d["analysis"] = ""
    if d.get("draft_body") is None:
        d["draft_body"] = d.get("reply", "") or ""


def friendly_sal_api_message(exc: BaseException) -> Optional[str]:
    """Operator-facing hint for common xAI / OpenAI client failures (no secrets)."""
    # APITimeoutError subclasses APIConnectionError in openai-python — check timeout first.
    if isinstance(exc, APITimeoutError):
        return "Timeout: Grok request timed out. Try again with less evidence or a shorter summary."
    if isinstance(exc, APIConnectionError):
        return "Connection to Grok failed. Check your network and try again."
    if isinstance(exc, AuthenticationError):
        return "Grok API key rejected. Check XAI_API_KEY in .env."
    if isinstance(exc, RateLimitError):
        return "Rate limit: Grok asks you to slow down; wait and retry."
    if isinstance(exc, InternalServerError):
        return "Grok returned a server error. Retry shortly."
    msg = str(exc)
    if "no completion choices" in msg.lower() or "empty response" in msg.lower():
        return "Grok returned an empty response. Try again."
    cur: Optional[BaseException] = exc
    while cur is not None:
        if isinstance(cur, APIStatusError):
            code = getattr(getattr(cur, "response", None), "status_code", None)
            if code:
                return f"Grok API HTTP error ({code}). Check credentials and service status."
        cur = cur.__cause__
    return msg or "Grok request failed."


@lru_cache(maxsize=1)
def _sal_body_cached() -> str:
    return load_sal_behavioral_text()


def _system_for_profile(assistant_profile: str) -> str:
    """Sal file + JSON API contract when present; else legacy inline prompts."""
    body = _sal_body_cached()
    if body.strip():
        return (
            body
            + json_tool_contract_suffix(state_codes_csv=_STATE_CODES_S)
            + run_mode_suffix(assistant_profile=assistant_profile)
        )
    if assistant_profile == "business_counsel":
        return SYSTEM_PROMPT_BUSINESS
    return SYSTEM_PROMPT_DISPUTE


def _sleep_backoff(attempt: int) -> None:
    delay = API_BASE_DELAY_SEC * (2**attempt) + random.uniform(0, 0.5)
    time.sleep(delay)


def analyze_and_draft(
    evidence_json: str,
    claim: str,
    *,
    assistant_profile: str = "dispute",
    state_hint: str = "",
) -> Dict[str, Any]:
    """
    Call Grok with structured JSON output. Returns dict with analysis, draft_body, citations,
    primary_state (canonical CO|FL|AZ|TX|NE or "", for review file subfolders).
    If state_hint is a valid code, it overrides model output (user-selected job site).
    assistant_profile: "dispute" | "business_counsel"
    """
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        raise ValueError("Set environment variable XAI_API_KEY for Grok.")

    model = os.environ.get("GROK_MODEL", GROK_MODEL)
    client = OpenAI(api_key=api_key, base_url=GROK_BASE_URL)

    forced_state = normalize_primary_state(state_hint)
    state_line = ""
    if forced_state:
        state_line = (
            f'\nOperator selected primary_state "{forced_state}" for file routing only (not a legal '
            f'conclusion). Your JSON must include primary_state exactly "{forced_state}".\n'
        )

    max_out = int(os.environ.get("GROK_MAX_OUTPUT_TOKENS", "1200"))

    if assistant_profile == "business_counsel":
        system = _system_for_profile(assistant_profile)
        user_content = (
            f"Evidence: {evidence_json}\n"
            f"Summary / instruction: {claim}\n"
            f"{state_line}"
            "Draft appropriate email content."
        )
    else:
        system = _system_for_profile(assistant_profile)
        user_content = (
            f"Evidence: {evidence_json}\nClaim: {claim}\n"
            f"{state_line}"
            "Draft rebuttal."
        )

    last_err: Optional[str] = None
    for attempt in range(API_MAX_RETRIES):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.3,
                max_tokens=max_out,
                response_format={"type": "json_object"},
            )
            usage = getattr(resp, "usage", None)

            text = (resp.choices[0].message.content or "{}").strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
                text = re.sub(r"\s*```\s*$", "", text)
            try:
                data, _mode = _parse_sal_response_json(text)
            except RuntimeError as e:
                preview = (text[:280] + "…") if len(text) > 280 else text
                raise RuntimeError(
                    "Grok returned content that is not valid JSON. Try again, shorten evidence, "
                    f"or switch model. Raw preview: {preview!r}"
                ) from e
            _normalize_sal_fields(data)
            if "citations" not in data:
                data["citations"] = []
            inferred = normalize_primary_state(data.get("primary_state"))
            data["primary_state"] = forced_state if forced_state else inferred
            extra = {"model": model, "assistant_profile": assistant_profile}
            if usage:
                extra["prompt_tokens"] = getattr(usage, "prompt_tokens", None)
                extra["completion_tokens"] = getattr(usage, "completion_tokens", None)
            if data["primary_state"]:
                extra["primary_state"] = data["primary_state"]
            log_event("grok_success", extra=extra)
            return data
        except Exception as e:
            last_err = str(e)
            log_event("grok_error", extra={"attempt": attempt}, error=last_err)
            if attempt < API_MAX_RETRIES - 1:
                _sleep_backoff(attempt)
            else:
                raise RuntimeError(
                    f"Grok failed after {API_MAX_RETRIES} tries: {last_err}"
                ) from e
