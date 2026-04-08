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

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    InternalServerError,
    OpenAI,
    RateLimitError,
)

from config import (
    API_BASE_DELAY_SEC,
    API_MAX_RETRIES,
    GROK_BASE_URL,
    GROK_MODEL,
    JOB_SITE_STATE_CODES,
    normalize_primary_state,
)
from logger_util import log_event
from sal_prompt import (
    json_tool_contract_suffix,
    load_sal_behavioral_text,
    run_mode_suffix,
)

_STATE_CODES_S = ", ".join(JOB_SITE_STATE_CODES)

def _strip_leading_bom(text: str) -> str:
    return text.lstrip("\ufeff")


def _strip_outer_json_fence(text: str) -> str:
    s = text.strip()
    if not s.startswith("```"):
        return text
    s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s*```\s*$", "", s)
    return s


def _extract_first_json_object(text: str) -> tuple[str, str]:
    """
    Return (slice, mode) where mode is 'direct' if the whole (trimmed, unfenced) string
    parsed as JSON, else 'extracted' when a leading object substring was used.
    """
    raw = _strip_leading_bom(text).strip()
    unfenced = _strip_outer_json_fence(raw)
    candidate = unfenced.strip()
    try:
        parsed = json.loads(candidate)
        if isinstance(parsed, dict):
            return candidate, "direct"
    except json.JSONDecodeError:
        pass

    start = candidate.find("{")
    if start < 0:
        raise RuntimeError("No JSON object found in model response.") from None

    depth = 0
    in_str = False
    esc = False
    quote = ""
    for i in range(start, len(candidate)):
        ch = candidate[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == quote:
                in_str = False
                quote = ""
            continue
        if ch in "\"'":
            in_str = True
            quote = ch
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                slice_ = candidate[start : i + 1]
                try:
                    parsed2 = json.loads(slice_)
                except json.JSONDecodeError as e:
                    raise RuntimeError(
                        "Model returned text containing `{` but not valid JSON object."
                    ) from e
                if not isinstance(parsed2, dict):
                    raise RuntimeError("Extracted JSON value is not a JSON object.")
                return slice_, "extracted"
    raise RuntimeError("Unclosed JSON object in model response.") from None


def _parse_sal_response_json(raw: str) -> tuple[dict[str, Any], str]:
    slice_, mode = _extract_first_json_object(raw)
    try:
        data = json.loads(slice_)
    except json.JSONDecodeError as e:
        raise RuntimeError("Invalid JSON in Sal response.") from e
    if isinstance(data, list):
        raise RuntimeError("Expected a JSON object, not an array.")
    if not isinstance(data, dict):
        raise RuntimeError("Expected a JSON object.")
    return data, mode


def _normalize_sal_fields(data: dict[str, Any]) -> None:
    if "draft_body" not in data or data.get("draft_body") is None:
        data["draft_body"] = data.get("reply") or ""
    if data.get("draft_body") is None:
        data["draft_body"] = ""
    if "analysis" not in data or data.get("analysis") is None:
        data["analysis"] = ""
    if data.get("citations") is None:
        data["citations"] = []
    cit = data.get("citations")
    if isinstance(cit, str):
        data["citations"] = [cit] if cit else []


def friendly_sal_api_message(exc: BaseException) -> Optional[str]:
    """Operator-facing hint for common xAI / Grok client failures."""
    chain: list[BaseException] = []
    cur: Optional[BaseException] = exc
    seen: set[int] = set()
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        chain.append(cur)
        cur = cur.__cause__ or cur.__context__

    for err in chain:
        if isinstance(err, RuntimeError):
            low = str(err).lower()
            if "no completion choices" in low or "empty response" in low:
                return (
                    "Grok returned an empty completion. Check XAI_API_KEY, model name, "
                    "and try again."
                )
        if isinstance(err, APITimeoutError):
            return (
                "Timeout: Grok request timed out. Retry with less evidence or a shorter prompt."
            )
        if isinstance(err, APIConnectionError):
            return (
                "Connection to Grok failed. Check your network, VPN, and firewall, then retry."
            )
        if isinstance(err, AuthenticationError):
            return "Grok rejected the API key. Verify XAI_API_KEY in your environment."
        if isinstance(err, RateLimitError):
            return (
                "Rate limit: Grok is throttling requests. Wait briefly and retry, or reduce volume."
            )
        if isinstance(err, InternalServerError):
            return "Grok returned a server error (upstream). Retry after a short wait."
        if isinstance(err, APIStatusError):
            code = getattr(err.response, "status_code", None)
            if code is not None:
                return f"Grok API error (HTTP {code}). Check status.x.ai and your request."
            return "Grok API returned an error response. Check status.x.ai and your request."
    return None


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

            choices = getattr(resp, "choices", None) or []
            if not choices:
                raise RuntimeError(
                    "Grok returned no completion choices (empty response)."
                )
            text = (choices[0].message.content or "").strip()
            try:
                data, _ = _parse_sal_response_json(text)
            except RuntimeError:
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
