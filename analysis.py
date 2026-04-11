"""
Grok (xAI) analysis + draft generation with exponential backoff retries.
"""
from __future__ import annotations

import sitepath

sitepath.ensure()

import json
import os
import random
import re
import time
from functools import lru_cache
from typing import Any, Dict, Optional

from openai import OpenAI

from logger_util import log_event
from sal.config import (
    API_BASE_DELAY_SEC,
    API_MAX_RETRIES,
    GROK_BASE_URL,
    GROK_MODEL,
    JOB_SITE_STATE_CODES,
    normalize_primary_state,
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
            if not resp.choices or not resp.choices[0].message.content:
                raise RuntimeError("Grok returned no completion choices (empty response).")
            text = resp.choices[0].message.content.strip()
            try:
                data, _mode = _parse_sal_response_json(text)
            except (json.JSONDecodeError, RuntimeError) as e:
                preview = (text[:280] + "…") if len(text) > 280 else text
                raise RuntimeError(
                    "Grok returned content that is not valid JSON. Try again, shorten evidence, "
                    f"or switch model. Raw preview: {preview!r}"
                ) from e
            _normalize_sal_fields(data)
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

def _parse_sal_response_json(raw: str) -> tuple[Dict[str, Any], str]:
    """Parse Sal JSON from model output. Returns (data, mode)."""
    text = (raw or "").strip()
    if not text:
        raise RuntimeError("Expected a JSON object, got empty string.")
    if text.startswith("\ufeff"):
        text = text.lstrip("\ufeff")
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```\s*$", "", text)
    mode = "direct"
    try:
        parsed: Any = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}", text, re.DOTALL)
        if not m:
            raise RuntimeError("Expected a JSON object but could not find one in model output.")
        mode = "extracted"
        parsed = json.loads(m.group(0))
    if isinstance(parsed, list):
        raise RuntimeError("Expected a JSON object, not an array.")
    if not isinstance(parsed, dict):
        raise RuntimeError("Expected a JSON object.")
    return parsed, mode


def _normalize_sal_fields(data: Dict[str, Any]) -> None:
    """Normalize Sal JSON fields in place."""
    if data.get("analysis") is None:
        data["analysis"] = ""
    if "draft_body" not in data or data.get("draft_body") is None:
        data["draft_body"] = data.pop("reply", "") or ""
    elif "reply" in data and "draft_body" not in data:
        data["draft_body"] = data.pop("reply", "") or ""
    cit = data.get("citations")
    if isinstance(cit, str):
        data["citations"] = [cit] if cit else []
    elif cit is None:
        data["citations"] = []


def friendly_sal_api_message(err: BaseException) -> str:
    """Map Grok/xAI errors to a short operator-facing string."""
    from openai import (
        APIConnectionError,
        APIStatusError,
        APITimeoutError,
        AuthenticationError,
        InternalServerError,
        RateLimitError,
    )

    chain: list[BaseException] = []
    cur: BaseException | None = err
    seen: set[int] = set()
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        chain.append(cur)
        nxt = cur.__cause__
        cur = nxt if isinstance(nxt, BaseException) else None

    for e in chain:
        if isinstance(e, APITimeoutError):
            return "Timeout talking to Grok. Try again with shorter evidence."
        if isinstance(e, APIConnectionError):
            return "Connection to Grok failed. Check network and try again."
        if isinstance(e, AuthenticationError):
            return "Authentication failed. Check your API key (XAI_API_KEY in .env)."
        if isinstance(e, RateLimitError):
            return "Rate limit from Grok. Wait and retry."
        if isinstance(e, InternalServerError):
            return "Grok server error. Try again later."
        if isinstance(e, APIStatusError):
            sc = getattr(getattr(e, "response", None), "status_code", None)
            if sc is not None:
                return f"Grok API error (HTTP {sc})."
            return "Grok API error."
        msg = str(e)
        if "no completion choices" in msg.lower() or "empty response" in msg.lower():
            return "Grok returned no usable completion. Try again."
    return f"Grok error: {err!s}"

