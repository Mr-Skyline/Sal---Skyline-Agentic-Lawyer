"""
Gmail search/thread fetch, pasted text parsing, GLM-OCR screenshots, merge.
"""
from __future__ import annotations

import base64
import json
import os
import pickle
import re
import tempfile
import webbrowser
import wsgiref.simple_server
import wsgiref.util
from email.header import decode_header, make_header
from typing import Any, Dict, List, Optional, Tuple

from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from oauthlib.oauth2.rfc6749.errors import MismatchingStateError

from .config import (
    CREDENTIALS_FILE,
    GMAIL_SCOPES,
    OAUTH_LOCAL_PORT,
    OAUTH_LOCAL_PORT_TRY_COUNT,
    OAUTH_LOOPBACK_HOST,
    OAUTH_OPEN_BROWSER,
    TOKEN_FILE,
)
from .gmail_retry import gmail_execute
from .logger_util import log_event


def _oauth_port_in_use(err: OSError) -> bool:
    win = getattr(err, "winerror", None)
    errno_val = getattr(err, "errno", None)
    return (
        win == 10048
        or errno_val in (48, 98)
        or "address already in use" in str(err).lower()
    )


def _oauth_loopback_listen_and_fetch(
    flow: InstalledAppFlow,
    host: str,
    port: int,
    *,
    open_browser: bool,
    success_message: str = "The authentication flow has completed. You may close this window.",
    max_spurious_requests: int = 64,
    timeout_seconds: Optional[float] = None,
) -> Any:
    """
    Like google_auth_oauthlib's run_local_server, but:
    - Ignores stray HTTP hits (favicon, probes) until the redirect has code= or error=.
    - Rewrites only the scheme http->https for oauthlib (avoids corrupting ?code=... values).
    """
    holder: Dict[str, Optional[str]] = {"uri": None}

    def wsgi_app(environ, start_response):
        holder["uri"] = wsgiref.util.request_uri(environ)
        start_response("200 OK", [("Content-type", "text/plain; charset=utf-8")])
        return [success_message.encode("utf-8")]

    wsgiref.simple_server.WSGIServer.allow_reuse_address = False
    httpd = wsgiref.simple_server.make_server(host, port, wsgi_app)
    _, bound_port = httpd.server_address[:2]
    flow.redirect_uri = f"http://{host}:{bound_port}/"
    auth_url, _ = flow.authorization_url()

    if open_browser:
        webbrowser.open(auth_url, new=1, autoraise=True)
    print(f"Please visit this URL to authorize this application: {auth_url}")

    httpd.timeout = timeout_seconds
    remaining = max_spurious_requests
    try:
        while remaining > 0:
            remaining -= 1
            httpd.handle_request()
            uri = holder["uri"]
            if uri and ("code=" in uri or "error=" in uri):
                if uri.startswith("http://"):
                    auth_response = "https://" + uri[7:]
                else:
                    auth_response = uri
                try:
                    flow.fetch_token(authorization_response=auth_response)
                except MismatchingStateError as e:
                    raise RuntimeError(
                        "OAuth state mismatch (often an old Google auth tab or a reused URL). "
                        "Close every accounts.google.com and localhost OAuth tab, run again, and use "
                        "only the URL printed in this terminal for this run."
                    ) from e
                return flow.credentials
    finally:
        httpd.server_close()

    raise RuntimeError(
        "OAuth loopback: no redirect with code= or error= received (too many stray requests). "
        "Close extra browser tabs, do not reuse an old Google auth URL from a previous run, "
        "or set OAUTH_OPEN_BROWSER=0 and paste only the URL printed above into Chrome/Edge."
    )


def get_gmail_service():
    creds = None
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except GoogleAuthError as e:
                err = str(e).lower()
                if "invalid" in err or "unauthorized" in err:
                    raise RuntimeError(
                        "Gmail token refresh failed (often wrong client_secret or revoked client). "
                        "In Google Cloud → Credentials → open your Desktop OAuth client, copy the "
                        "current Client secret into credentials.json, delete token.pickle, retry."
                    ) from e
                raise
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"Missing {CREDENTIALS_FILE}. Add OAuth credentials.json."
                )
            with open(CREDENTIALS_FILE, encoding="utf-8") as cf:
                client_cfg = json.load(cf)
            if "web" not in client_cfg and "installed" not in client_cfg:
                raise RuntimeError(
                    "credentials.json must contain a 'web' or 'installed' OAuth client block."
                )
            try:
                # google_auth_oauthlib prefers "web" over "installed" if both exist; keep the same order.
                if "web" in client_cfg:
                    # Web client: redirect_uri must match Authorized redirect URIs in Cloud Console.
                    ports = [
                        OAUTH_LOCAL_PORT + i for i in range(OAUTH_LOCAL_PORT_TRY_COUNT)
                    ]
                    creds = None
                    last_os: Optional[OSError] = None
                    for port in ports:
                        try:
                            # Fresh Flow per port so OAuth state never crosses a failed attempt.
                            flow = InstalledAppFlow.from_client_config(
                                client_cfg, GMAIL_SCOPES
                            )
                            creds = _oauth_loopback_listen_and_fetch(
                                flow,
                                OAUTH_LOOPBACK_HOST,
                                port,
                                open_browser=OAUTH_OPEN_BROWSER,
                            )
                            break
                        except OSError as e:
                            if not _oauth_port_in_use(e):
                                raise
                            last_os = e
                    if creds is None:
                        lo, hi = ports[0], ports[-1]
                        sample = ", ".join(
                            f"http://{OAUTH_LOOPBACK_HOST}:{p}/" for p in ports[:3]
                        )
                        if len(ports) > 3:
                            sample += ", ..."
                        raise RuntimeError(
                            f"Tried loopback ports {lo}-{hi}; all in use. Close other programs using "
                            f"those ports, or set OAUTH_LOCAL_PORT / OAUTH_LOCAL_PORT_TRY_COUNT in .env. "
                            "For Web OAuth, add each redirect URI to Google Cloud → "
                            f"Credentials → your Web client (e.g. {sample}). "
                            "Run: py oauth_google_checklist.py — or switch to a Desktop OAuth client."
                        ) from last_os
                elif "installed" in client_cfg:
                    flow = InstalledAppFlow.from_client_config(
                        client_cfg, GMAIL_SCOPES
                    )
                    creds = _oauth_loopback_listen_and_fetch(
                        flow,
                        OAUTH_LOOPBACK_HOST,
                        0,
                        open_browser=OAUTH_OPEN_BROWSER,
                    )
            except GoogleAuthError as e:
                err = str(e).lower()
                if "invalid_client" in err or "unauthorized_client" in err:
                    raise RuntimeError(
                        "OAuth rejected the client (invalid_client). The client_id and client_secret "
                        "in credentials.json must be from the same Desktop OAuth client in Google Cloud. "
                        "Download the JSON again or paste both values from Credentials → your client."
                    ) from e
                raise
        try:
            with open(TOKEN_FILE, "wb") as f:
                pickle.dump(creds, f)
        except OSError as e:
            raise RuntimeError(
                f"Could not write token.pickle to {TOKEN_FILE.resolve()}: {e}. "
                "Check folder permissions; if the project folder is cloud-synced, pause sync on token.pickle."
            ) from e
        log_event("gmail_token_saved", extra={"path": str(TOKEN_FILE.resolve())})
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def _decode_mime_header(value: Optional[str]) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def _parse_gmail_message_payload(payload: Dict[str, Any], depth: int = 0) -> str:
    if depth > 20:
        return ""
    parts: List[str] = []
    if "body" in payload and payload["body"].get("data"):
        try:
            raw = base64.urlsafe_b64decode(payload["body"]["data"]).decode(
                "utf-8", errors="replace"
            )
            parts.append(raw)
        except Exception:
            pass
    for p in payload.get("parts") or []:
        mime = p.get("mimeType", "")
        if mime in ("text/plain", "text/html"):
            if p.get("body", {}).get("data"):
                try:
                    raw = base64.urlsafe_b64decode(p["body"]["data"]).decode(
                        "utf-8", errors="replace"
                    )
                    parts.append(raw)
                except Exception:
                    pass
        elif "parts" in p:
            parts.append(_parse_gmail_message_payload(p, depth + 1))
    return "\n".join(s for s in parts if s)


def _headers_dict(headers: Optional[List[Dict[str, str]]]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for h in headers or []:
        name = (h.get("name") or "").lower()
        out[name] = h.get("value") or ""
    return out


def claim_to_query_keywords(claim: str, max_words: int = 6) -> str:
    stop = {
        "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "as", "is", "was", "are", "were", "be", "been", "being", "have",
        "has", "had", "do", "does", "did", "will", "would", "could", "should",
        "i", "you", "he", "she", "it", "we", "they", "me", "my", "not", "no",
    }
    words = re.findall(r"[a-zA-Z0-9']+", claim.lower())
    picked = [w for w in words if w not in stop and len(w) > 1][:max_words]
    return " ".join(picked)


def fetch_messages_for_evidence(
    service,
    target_email: str,
    claim: str,
    thread_id: Optional[str] = None,
    max_messages: int = 40,
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Returns (evidence_rows, query_description) for UI hints when the list is empty.
    """
    out: List[Dict[str, Any]] = []
    msg_ids: List[str] = []
    query_description = ""

    if thread_id:
        query_description = f"thread:{thread_id}"
        try:
            thr = gmail_execute(
                service.users()
                .threads()
                .get(userId="me", id=thread_id, format="full")
            )
        except HttpError as e:
            status = getattr(e.resp, "status", None) or 0
            if status == 404:
                raise RuntimeError(
                    f"Gmail thread not found (check the ID from the URL …/thread/…): {thread_id!r}"
                ) from e
            raise
        for m in thr.get("messages") or []:
            msg_ids.append(m["id"])
    else:
        kw = claim_to_query_keywords(claim)
        q_parts = [f"(from:{target_email} OR to:{target_email})"]
        if kw:
            q_parts.append(kw)
        q = " ".join(q_parts)
        query_description = q
        lst = gmail_execute(
            service.users()
            .messages()
            .list(userId="me", q=q, maxResults=min(max_messages, 100))
        )
        for m in lst.get("messages") or []:
            msg_ids.append(m["id"])

    for mid in msg_ids[:max_messages]:
        full = gmail_execute(
            service.users().messages().get(userId="me", id=mid, format="full")
        )
        pl = full.get("payload") or {}
        h = _headers_dict(pl.get("headers"))
        date_s = h.get("date", "")
        from_s = _decode_mime_header(h.get("from", ""))
        to_s = _decode_mime_header(h.get("to", ""))
        subj = _decode_mime_header(h.get("subject", ""))
        body = _parse_gmail_message_payload(pl)
        snippet = full.get("snippet") or ""
        text = body.strip() or snippet
        att_names: List[str] = []
        for part in pl.get("parts") or []:
            if part.get("filename"):
                att_names.append(part["filename"])
        out.append(
            {
                "source": "gmail",
                "date": date_s,
                "sender": from_s,
                "recipient": to_s,
                "subject": subj,
                "text": text[:50000],
                "message_id": mid,
                "thread_id": full.get("threadId", ""),
                "attachments": att_names,
                "proof": f"gmail:message:{mid}",
            }
        )
    return out, query_description


PASTE_PATTERNS = [
    re.compile(
        r"^(?P<date>\d{1,2}/\d{1,2}/\d{2,4})\s+(?P<dir>From|To):\s*(?P<who>.+?)\s*[-–—]\s*(?P<text>.+)$",
        re.I,
    ),
    re.compile(
        r"^(?P<date>\d{4}-\d{2}-\d{2})\s+\[(?P<dir>From|To)\]\s*(?P<who>.+?):\s*(?P<text>.+)$",
        re.I,
    ),
    re.compile(
        r"^\[(?P<date>[^\]]+)\]\s*(?P<who>.+?):\s*(?P<text>.+)$",
    ),
]


def parse_pasted_texts(pasted: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not pasted or not pasted.strip():
        return rows
    for line in pasted.splitlines():
        line = line.strip()
        if not line:
            continue
        matched = False
        for pat in PASTE_PATTERNS:
            m = pat.match(line)
            if m:
                d = m.groupdict()
                rows.append(
                    {
                        "source": "pasted",
                        "date": d.get("date", ""),
                        "sender": d.get("who", d.get("dir", "")),
                        "text": d.get("text", line),
                        "proof": "pasted:textarea",
                    }
                )
                matched = True
                break
        if not matched:
            rows.append(
                {
                    "source": "pasted",
                    "date": "",
                    "sender": "",
                    "text": line,
                    "proof": "pasted:textarea",
                }
            )
    return rows


_TS_LINE_RE = re.compile(
    r"\b(\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2}|\d{1,2}:\d{2}\s*(?:AM|PM)?)\b",
    re.I,
)


def _bbox_sort_key(bbox: Optional[List[Any]]) -> float:
    if not bbox or len(bbox) < 2:
        return 0.0
    try:
        return float(bbox[1])
    except (TypeError, ValueError):
        return 0.0


def _extract_timestamp_from_text(text: str) -> str:
    m = _TS_LINE_RE.search(text or "")
    return m.group(1) if m else ""


def parse_screenshots_with_glmocr(paths: List[str]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not paths:
        return rows

    try:
        from glmocr import GlmOcr
    except ImportError as e:
        raise ImportError(
            "pip install -r requirements-ocr.txt; set ZHIPU_API_KEY"
        ) from e

    api_key = os.environ.get("ZHIPU_API_KEY") or os.environ.get("GLMOCR_API_KEY")
    ctx = GlmOcr(api_key=api_key) if api_key else GlmOcr()
    with ctx as parser:
        for path in paths:
            result = parser.parse(path, save_layout_visualization=False)
            data = result.to_dict() if hasattr(result, "to_dict") else {}
            layout = data.get("layout_details") or data.get("layout") or []
            regions_flat: List[Dict[str, Any]] = []
            if isinstance(layout, list):
                for page_idx, page in enumerate(layout):
                    if isinstance(page, list):
                        for r in page:
                            if isinstance(r, dict):
                                rr = dict(r)
                                rr["_page"] = page_idx
                                regions_flat.append(rr)
                    elif isinstance(page, dict):
                        d = dict(page)
                        d["_page"] = page_idx
                        regions_flat.append(d)
            regions_flat.sort(
                key=lambda r: (
                    r.get("_page", 0),
                    _bbox_sort_key(r.get("bbox_2d") or r.get("bbox")),
                )
            )
            if regions_flat:
                for r in regions_flat:
                    content = (
                        r.get("content")
                        or r.get("text")
                        or r.get("markdown")
                        or ""
                    )
                    ts = _extract_timestamp_from_text(str(content))
                    rows.append(
                        {
                            "source": "screenshot",
                            "date": ts,
                            "sender": str(r.get("label", "") or ""),
                            "text": str(content).strip(),
                            "proof": path,
                        }
                    )
            else:
                md = getattr(result, "markdown_result", None) or data.get(
                    "markdown_result", ""
                )
                rows.append(
                    {
                        "source": "screenshot",
                        "date": _extract_timestamp_from_text(str(md)),
                        "sender": "",
                        "text": str(md).strip()[:20000],
                        "proof": path,
                    }
                )
    return rows


def merge_evidence_json(items: List[Dict[str, Any]]) -> str:
    return json.dumps(items, ensure_ascii=False)


_OCR_UPLOAD_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".pdf"}
_TEXT_DOC_EXT = {".txt", ".md", ".markdown", ".docx"}


def partition_evidence_upload_paths(
    paths: List[str],
) -> Tuple[List[str], List[str]]:
    """
    Split saved upload paths into (ocr_paths, document_paths).
    OCR paths go to GLM-OCR; document paths are read as text (incl. .docx).
    """
    ocr: List[str] = []
    docs: List[str] = []
    for p in paths:
        ext = os.path.splitext(p)[1].lower()
        if ext in _OCR_UPLOAD_EXT:
            ocr.append(p)
        elif ext in _TEXT_DOC_EXT:
            docs.append(p)
    return ocr, docs


def parse_document_files(paths: List[str]) -> List[Dict[str, Any]]:
    """Build evidence rows from plain-text and Word uploads."""
    rows: List[Dict[str, Any]] = []
    for p in paths:
        base = os.path.basename(p)
        ext = os.path.splitext(p)[1].lower()
        text = ""
        if ext in (".txt", ".md", ".markdown"):
            try:
                with open(p, encoding="utf-8", errors="replace") as f:
                    text = f.read()
            except OSError:
                continue
        elif ext == ".docx":
            try:
                from docx import Document as DocxDocument

                doc = DocxDocument(p)
                text = "\n".join(
                    para.text for para in doc.paragraphs if para.text.strip()
                )
            except ImportError:
                rows.append(
                    {
                        "source": "document",
                        "date": "",
                        "sender": base,
                        "text": (
                            f"[Word file {base}: add `python-docx` to read text, "
                            "or export to PDF.]"
                        ),
                        "proof": f"upload:{base}",
                    }
                )
                continue
            except Exception:
                continue
        if text.strip():
            rows.append(
                {
                    "source": "document",
                    "date": "",
                    "sender": base,
                    "text": text[:50000],
                    "proof": f"upload:{base}",
                }
            )
    return rows


def save_uploaded_files(uploaded_files) -> List[str]:
    paths: List[str] = []
    if not uploaded_files:
        return paths
    tmp = tempfile.mkdtemp(prefix="dispute_screens_")
    for uf in uploaded_files:
        p = os.path.join(tmp, uf.name)
        with open(p, "wb") as f:
            f.write(uf.getbuffer())
        paths.append(p)
    return paths
