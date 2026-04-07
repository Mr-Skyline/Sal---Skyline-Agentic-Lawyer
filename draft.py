"""
Build MIME Gmail draft with reply headers, optional attachments, Dispute Draft label.
"""
from __future__ import annotations

import base64
import mimetypes
import os
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional, Tuple

from gmail_retry import gmail_execute
from logger_util import log_event

DISPUTE_LABEL_NAME = "Dispute Draft"


def _get_header(headers: Optional[List[Dict[str, str]]], name: str) -> str:
    if not headers:
        return ""
    name_l = name.lower()
    for h in headers:
        if (h.get("name") or "").lower() == name_l:
            return h.get("value") or ""
    return ""


def thread_reply_headers(
    service, thread_id: str
) -> Tuple[str, str, str, List[str]]:
    """
    Return (subject, in_reply_to, references, message_ids_newest_first)
    for the thread's latest message suitable for a reply.
    """
    thr = gmail_execute(
        service.users().threads().get(userId="me", id=thread_id, format="full")
    )
    messages = list(thr.get("messages") or [])
    if not messages:
        return "Re: Dispute clarification", "", "", []

    messages.sort(key=lambda m: int(m.get("internalDate", 0)))
    ids_chrono = [m["id"] for m in messages]
    msg_ids: List[str] = []
    subj = "Re: Dispute clarification"
    for mid in ids_chrono:
        full = gmail_execute(
            service.users().messages().get(userId="me", id=mid, format="full")
        )
        pl = full.get("payload") or {}
        hdrs = pl.get("headers") or []
        mid_hdr = _get_header(hdrs, "Message-ID")
        if mid_hdr:
            msg_ids.append(mid_hdr)
        s = _get_header(hdrs, "Subject")
        if s:
            subj = s
    if not subj.lower().startswith("re:"):
        subj = f"Re: {subj}"
    latest = msg_ids[-1] if msg_ids else ""
    references = " ".join(msg_ids) if msg_ids else ""
    return subj, latest, references, msg_ids


def ensure_label_id(service, label_name: str = DISPUTE_LABEL_NAME) -> str:
    lst = gmail_execute(service.users().labels().list(userId="me"))
    for lab in lst.get("labels") or []:
        if lab.get("name") == label_name:
            return lab["id"]
    body = {
        "name": label_name,
        "labelListVisibility": "labelShow",
        "messageListVisibility": "show",
    }
    created = gmail_execute(service.users().labels().create(userId="me", body=body))
    return created["id"]


def build_raw_mime(
    draft_body: str,
    subject: str,
    in_reply_to: str,
    references: str,
    attachment_paths: Optional[List[str]] = None,
) -> str:
    """RFC822 message as string; will be base64url-encoded for Gmail API."""
    attachment_paths = attachment_paths or []
    if attachment_paths:
        root = MIMEMultipart("mixed")
    else:
        root = MIMEMultipart("alternative")

    root["Subject"] = subject
    if in_reply_to:
        root["In-Reply-To"] = in_reply_to
    if references:
        root["References"] = references

    if attachment_paths:
        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText(draft_body, "plain", "utf-8"))
        root.attach(alt)
        for path in attachment_paths:
            if not path or not os.path.isfile(path):
                continue
            ctype, _ = mimetypes.guess_type(path)
            if not ctype:
                ctype = "application/octet-stream"
            maintype, subtype = ctype.split("/", 1)
            with open(path, "rb") as f:
                data = f.read()
            if maintype == "image":
                part = MIMEImage(data, _subtype=subtype)
            else:
                part = MIMEApplication(data, _subtype=subtype)
            part.add_header(
                "Content-Disposition",
                "attachment",
                filename=os.path.basename(path),
            )
            root.attach(part)
    else:
        root.attach(MIMEText(draft_body, "plain", "utf-8"))

    return root.as_string()


def create_gmail_draft(
    service,
    draft_body: str,
    thread_id: Optional[str],
    proof_paths: Optional[List[str]] = None,
    subject_override: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a Gmail draft; optionally reply in-thread with In-Reply-To/References.
    Attaches proof files (screenshots). Applies label Dispute Draft.
    """
    proof_paths = [p for p in (proof_paths or []) if p and os.path.isfile(p)]
    in_reply_to = ""
    references = ""

    if thread_id:
        subj, in_reply_to, references, _ = thread_reply_headers(service, thread_id)
    else:
        custom = (subject_override or "").strip()
        if custom:
            subj = custom if custom.lower().startswith("re:") else f"Re: {custom}"
        else:
            subj = "Draft — Elite Business Counsel"

    raw_str = build_raw_mime(
        draft_body, subj, in_reply_to, references, proof_paths or None
    )
    raw_b64 = base64.urlsafe_b64encode(raw_str.encode("utf-8")).decode("ascii")

    body: Dict[str, Any] = {"message": {"raw": raw_b64}}
    if thread_id:
        body["message"]["threadId"] = thread_id

    draft = gmail_execute(service.users().drafts().create(userId="me", body=body))
    draft_id = draft.get("id", "")
    msg = draft.get("message") or {}
    message_id = msg.get("id", "")

    label_id = ensure_label_id(service)
    if message_id:
        gmail_execute(
            service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"addLabelIds": [label_id]},
            )
        )

    log_event(
        "draft_created",
        extra={"draft_id": draft_id, "message_id": message_id, "thread_id": thread_id or ""},
    )
    return {"draft_id": draft_id, "message_id": message_id, "thread_id": msg.get("threadId", "")}
