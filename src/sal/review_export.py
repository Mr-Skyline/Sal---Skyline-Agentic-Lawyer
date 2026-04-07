"""
Write Streamlit pipeline output to SKYLINE_REVIEW_DIR as Markdown (Sal workflow).
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import SKYLINE_REVIEW_DIR, review_state_subdir
from .db import insert_review_export_meta


def _slug(text: str, max_len: int = 48) -> str:
    t = re.sub(r"[^\w\-]+", "_", text.strip(), flags=re.UNICODE)
    t = re.sub(r"_+", "_", t).strip("_").lower()
    return (t[:max_len] or "matter").rstrip("_")


def default_client_label(target_email: str) -> str:
    """Domain host before first dot, e.g. name@acme.com → acme."""
    email = target_email.strip().lower()
    if "@" in email:
        domain = email.split("@", 1)[1]
        host = domain.split(".")[0] if domain else domain
        return _slug(host, 32)
    return _slug(email, 32)


def default_issue_keyword(claim: str) -> str:
    line = claim.replace("\n", " ").strip()
    words = line.split()[:6]
    return _slug(" ".join(words), 36) if words else "matter"


def _review_filename(
    client_label: str,
    issue_keyword: str,
    when: Optional[datetime] = None,
) -> str:
    """Sal pattern: {YYYY-MM-DD}_{ClientOrProjectShortName}_{IssueTypeKeyword}.md"""
    dt = when or datetime.now(timezone.utc)
    date_s = dt.strftime("%Y-%m-%d")
    return f"{date_s}_{_slug(client_label, 32)}_{_slug(issue_keyword, 36)}.md"


def export_analysis_markdown(
    *,
    client_label: str,
    issue_keyword: str,
    claim: str,
    assistant_profile: str,
    result: Dict[str, Any],
    target_email: str,
    evidence_excerpt: str = "",
) -> Path:
    """
    Create SKYLINE_REVIEW_DIR if needed. Writes under SKYLINE_REVIEW_DIR/<state>/<file>.md
    where <state> is model-inferred primary_state (or _unspecified). Appends if file exists.

    Returns path written. Raises OSError on filesystem errors.
    """
    analysis = (result.get("analysis") or "").strip()
    draft = (result.get("draft_body") or "").strip()
    cites: List[str] = list(result.get("citations") or [])

    state_folder = review_state_subdir(str(result.get("primary_state") or ""))
    out_dir = SKYLINE_REVIEW_DIR / state_folder
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / _review_filename(client_label, issue_keyword)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    excerpt = (evidence_excerpt or "").strip()
    if len(excerpt) > 600:
        excerpt = excerpt[:597] + "…"

    cite_block = "\n".join(f"- {c}" for c in cites) if cites else "_None returned._"
    ps = (result.get("primary_state") or "").strip().upper()
    state_hdr = (
        f"**Primary state (model-inferred, for filing only):** {ps}\n"
        if ps
        else "**Primary state (model-inferred):** *(not specified — stored in _unspecified subfolder)*\n"
    )

    section = f"""## Analysis (Grok)

{analysis or "_No analysis returned._"}

## Draft for review

{draft or "_No draft returned._"}

## Citations

{cite_block}
"""

    footer = "\n---\n*Exported from Elite Business Counsel (internal workspace). Not legal advice.*\n"

    if path.exists():
        append_block = f"""

---

## Update {now}

{section}"""
        try:
            path.write_text(
                path.read_text(encoding="utf-8") + append_block, encoding="utf-8"
            )
        except OSError as e:
            raise OSError(f"Could not append review file {path}: {e}") from e
        insert_review_export_meta(
            primary_state=ps if ps else None,
            state_subdir=state_folder,
            file_name=path.name,
        )
        return path

    body = f"""# Skyline matter review

**Analysis timestamp:** {now}
**Counterparty / thread context:** `{target_email.strip()}`
{state_hdr}**Matter summary (intake):** {claim.strip()}
**Drafting posture:** `{assistant_profile}`

> **Key excerpt (evidence preview):** {excerpt or "_No excerpt passed._"}

{section}{footer}"""
    try:
        path.write_text(body, encoding="utf-8")
    except OSError as e:
        raise OSError(f"Could not write review file {path}: {e}") from e
    insert_review_export_meta(
        primary_state=ps if ps else None,
        state_subdir=state_folder,
        file_name=path.name,
    )
    return path
