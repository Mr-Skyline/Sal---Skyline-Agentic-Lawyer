"""
Dispute Agent Elite — Streamlit UI: evidence + Grok draft + Gmail draft.
Run: py -m streamlit run main.py
     (On Windows, `streamlit` alone may not be on PATH.)
"""
from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv

from analysis import analyze_and_draft
from config import (
    CREDENTIALS_FILE,
    INTENDED_PROJECT_ROOT,
    JOB_SITE_STATE_CODES,
    LOG_FILE,
    ROOT,
    SKYLINE_REVIEW_DIR,
    TOKEN_FILE,
)
from review_export import (
    default_client_label,
    default_issue_keyword,
    export_analysis_markdown,
)
from draft import create_gmail_draft
from evidence import (
    fetch_messages_for_evidence,
    get_gmail_service,
    merge_evidence_json,
    parse_document_files,
    parse_pasted_texts,
    parse_screenshots_with_glmocr,
    partition_evidence_upload_paths,
    save_uploaded_files,
)
from logger_util import log_event
from secrets_store import save_api_keys_to_dotenv, save_gmail_credentials_json
from verify_setup import run_checks

load_dotenv(ROOT / ".env", override=True)

# --- Session state (before widgets) ---
if "last_grok" not in st.session_state:
    st.session_state.last_grok = None
if "last_evidence_items" not in st.session_state:
    st.session_state.last_evidence_items = []
if "last_evidence_paths" not in st.session_state:
    st.session_state.last_evidence_paths = []
if "draft_preview" not in st.session_state:
    st.session_state.draft_preview = ""

st.set_page_config(
    page_title="Elite Business Counsel",
    layout="wide",
    page_icon="⚖️",
    initial_sidebar_state="collapsed",
)

cred_ok = CREDENTIALS_FILE.exists()
tok_ok = TOKEN_FILE.exists()
xai_ok = bool(os.environ.get("XAI_API_KEY"))
ocr_ok = bool(os.environ.get("ZHIPU_API_KEY") or os.environ.get("GLMOCR_API_KEY"))
ready = cred_ok and tok_ok and xai_ok


def _inject_theme_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&family=Source+Sans+3:wght@400;500;600&display=swap');
        html, body, [data-testid="stAppViewContainer"] {
            font-family: 'Source Sans 3', 'Segoe UI', sans-serif;
        }
        h1, h2, h3, [data-testid="stHeader"] {
            font-family: 'Cormorant Garamond', Georgia, serif !important;
        }
        [data-testid="stHeader"] {
            background: linear-gradient(90deg, #0a0a0a 0%, #1a1612 45%, #0a0a0a 100%);
            border-bottom: 1px solid rgba(201, 162, 39, 0.35);
        }
        [data-testid="stSidebar"] > div:first-child {
            background: linear-gradient(165deg, #141414 0%, #0c0c0c 100%);
            border-right: 1px solid rgba(201, 162, 39, 0.18);
        }
        .block-container {
            padding-top: 1.5rem;
        }
        div[data-testid="stExpander"] details {
            border: 1px solid rgba(201, 162, 39, 0.22);
            border-radius: 10px;
            background: rgba(22, 22, 22, 0.55);
        }
        [data-testid="stForm"] {
            border: 1px solid rgba(201, 162, 39, 0.22);
            border-radius: 14px;
            padding: 1.25rem 1.5rem;
            background: rgba(20, 20, 20, 0.75);
        }
        hr {
            border-color: rgba(201, 162, 39, 0.2) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


_inject_theme_css()

# --- Minimal sidebar (navigation + one-line cue) ---
with st.sidebar:
    st.markdown("### Elite Business Counsel")
    st.caption("Primary workspace is the main panel. Technical setup lives at the bottom.")
    if ready:
        st.success("Connectivity ready.")
    else:
        st.warning("Action required — see alerts above the form or open **Administrator** below.")

# --- Hero ---
st.markdown(
    """
    <div style="margin-bottom: 1.25rem;">
        <p style="color: #C9A227; font-size: 0.75rem; letter-spacing: 0.28em; text-transform: uppercase; margin: 0 0 0.35rem 0;">Confidential workspace</p>
        <h1 style="margin: 0; font-weight: 600; color: #F5F2EB;">Elite Business Counsel</h1>
        <p style="color: #9a9590; margin: 0.5rem 0 0 0; max-width: 42rem;">
            Structured correspondence and dispute drafting with Gmail context, document intake, and Grok-assisted analysis.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

if not ready:
    if not xai_ok:
        st.error("Configure **XAI_API_KEY** (Grok) to run analysis — use **Administrator** below or `.env`.")
    if not cred_ok:
        st.error("Add **credentials.json** (Google Desktop OAuth client).")
    if not tok_ok:
        st.warning("Complete Gmail sign-in once: from this folder run **`py oauth_login.py`**.")

with st.expander("Legal notice", expanded=False):
    st.caption(
        "This software does not provide legal advice. It assists with drafting and organization only. "
        "Engage qualified counsel for advice, strategy, filings, and regulated matters."
    )

st.divider()

# --- Main matter form ---
st.markdown("##### Matter intake")
st.caption(
    "Provide the counterparty and a concise summary. Optionally lock **project state** below so review files "
    "land under `SKYLINE_REVIEW_DIR/CO` (or FL, AZ, TX, NE); otherwise Grok infers `primary_state` from context "
    "and ambiguous matters go to `_unspecified`."
)

with st.form("case_form", clear_on_submit=False):
    target_email = st.text_input(
        "Counterparty email",
        placeholder="name@company.com",
        help="Gmail search uses messages to or from this address, refined by your summary.",
    )
    claim = st.text_area(
        "Matter summary",
        height=140,
        placeholder="Facts, positions, and distinctive phrases that appear in the emails you want retrieved.",
        help="Used for search keywords and as the instruction to the drafting model.",
    )
    with st.expander("Review file naming (optional)", expanded=False):
        st.caption(
            "After **Analyze & draft**, a Markdown record is saved under **SKYLINE_REVIEW_DIR** in a subfolder "
            "for that matter’s state (see **Project state** above, or Grok-inferred CO/FL/AZ/TX/NE, else `_unspecified`). "
            "Leave blank to auto-fill client/issue from counterparty email and summary."
        )
        review_client = st.text_input(
            "Client / project short name",
            placeholder="e.g. AcmeGC or job nickname",
            key="review_client",
        )
        review_issue = st.text_input(
            "Issue keyword",
            placeholder="e.g. payment or lien-notice",
            key="review_issue",
        )

    with st.expander("Documents & exhibits", expanded=False):
        st.caption(
            "Drop contracts, letters, notes, or images. Text files and Word documents are read directly; "
            "images and PDFs use OCR when a ZHIPU / GLM-OCR key is configured."
        )
        evidence_files = st.file_uploader(
            "Upload files",
            type=[
                "png",
                "jpg",
                "jpeg",
                "webp",
                "gif",
                "pdf",
                "txt",
                "md",
                "docx",
            ],
            accept_multiple_files=True,
            label_visibility="collapsed",
            help="Attachments can be included when you create a Gmail draft.",
        )
        pasted_texts = st.text_area(
            "Additional notes or pasted excerpts",
            height=120,
            placeholder="Optional context not present in Gmail or files.",
            label_visibility="visible",
        )

    with st.expander("Gmail threading (optional)", expanded=False):
        thread_id = st.text_input(
            "Thread ID",
            placeholder="From Gmail URL …/thread/XXXXXXXX",
            help="Scopes retrieval to this thread and sets reply headers for drafts.",
        )
        draft_subject = st.text_input(
            "New draft subject",
            placeholder="Only when not replying in an existing thread",
            help="Used for a standalone Gmail draft when Thread ID is empty.",
        )

    assistant_profile = st.selectbox(
        "Drafting posture",
        options=["dispute", "business_counsel"],
        format_func=lambda x: (
            "Dispute — rigorous, contradiction-aware"
            if x == "dispute"
            else "Business counsel — commercial, measured tone"
        ),
        help="Adjusts model instructions only.",
    )
    job_site_state = st.selectbox(
        "Project state (job site)",
        options=("",) + JOB_SITE_STATE_CODES,
        format_func=lambda x: "Let Grok infer from context" if x == "" else x,
        help="Locks which subfolder under SKYLINE_REVIEW_DIR receives the review Markdown (record-keeping only).",
    )

    col_a, col_b = st.columns([1, 1])
    with col_a:
        analyze_submitted = st.form_submit_button("Analyze & draft", type="primary", use_container_width=True)
    with col_b:
        st.caption("Retrieves Gmail evidence, processes uploads, then runs Grok.")

draft_row = st.columns([1, 2])
with draft_row[0]:
    draft_btn = st.button(
        "Create Gmail draft",
        use_container_width=True,
        help="Sends the text from the Draft panel below (and attaches uploaded files when possible).",
    )

st.divider()

if analyze_submitted:
    if not target_email.strip() or not claim.strip():
        st.error("Counterparty email and matter summary are required.")
    else:
        items = []
        evidence_paths: list[str] = []
        try:
            with st.spinner("Connecting to Gmail…"):
                service = get_gmail_service()
            with st.spinner("Retrieving messages…"):
                q_frag = f"from:{target_email.strip()} OR to:{target_email.strip()}"
                log_event(
                    "gmail_evidence_start",
                    extra={"query_fragment": q_frag, "thread_id": thread_id.strip() or None},
                )
                gmail_items, gmail_query = fetch_messages_for_evidence(
                    service,
                    target_email.strip(),
                    claim,
                    thread_id.strip() or None,
                )
                items.extend(gmail_items)
            if gmail_items:
                st.success(f"Retrieved **{len(gmail_items)}** message(s) from Gmail.")
            else:
                st.warning(
                    f"No Gmail matches for: `{gmail_query}`. "
                    "Refine the address or summary, or set a **Thread ID** under Gmail threading."
                )

            pasted_items = parse_pasted_texts(pasted_texts)
            items.extend(pasted_items)

            if evidence_files:
                evidence_paths = save_uploaded_files(evidence_files)
                ocr_paths, doc_paths = partition_evidence_upload_paths(evidence_paths)
                if doc_paths:
                    items.extend(parse_document_files(doc_paths))
                if ocr_paths:
                    if not ocr_ok:
                        st.warning(
                            "Images/PDFs need **ZHIPU_API_KEY** or **GLMOCR_API_KEY** for OCR. "
                            "Text and Word files were still processed."
                        )
                    else:
                        with st.spinner("Extracting text from images and PDFs…"):
                            ocr_items = parse_screenshots_with_glmocr(ocr_paths)
                            items.extend(ocr_items)
                        st.success(f"OCR: **{len(ocr_items)}** segment(s) added.")

            evidence_json = merge_evidence_json(items)
            st.session_state.last_evidence_items = items
            st.session_state.last_evidence_paths = evidence_paths

            with st.spinner("Drafting with Grok…"):
                result = analyze_and_draft(
                    evidence_json,
                    claim,
                    assistant_profile=assistant_profile,
                    state_hint=job_site_state,
                )
            st.session_state.last_grok = result
            st.session_state.draft_preview = result.get("draft_body", "") or ""
            log_event(
                "pipeline_analyze_done",
                extra={
                    "evidence_count": len(items),
                    "state_locked": bool(job_site_state.strip()),
                },
            )
            cl = (review_client or "").strip() or default_client_label(target_email)
            ik = (review_issue or "").strip() or default_issue_keyword(claim)
            try:
                excerpt = ""
                for row in items:
                    t = (row.get("text") or "").strip()
                    if t:
                        excerpt = t[:900] + ("…" if len(t) > 900 else "")
                        break
                out_path = export_analysis_markdown(
                    client_label=cl,
                    issue_keyword=ik,
                    claim=claim,
                    assistant_profile=assistant_profile,
                    result=result,
                    target_email=target_email.strip(),
                    evidence_excerpt=excerpt,
                )
                ps = (result.get("primary_state") or "").strip().upper() or None
                log_event(
                    "review_markdown_export",
                    extra={
                        "path": str(out_path),
                        "client_label": cl,
                        "issue_keyword": ik,
                        "primary_state": ps,
                    },
                )
                st.success("Analysis complete — review **Deliverables** below.")
                st.info(f"Review record saved: `{out_path}`")
            except OSError as oe:
                log_event("review_markdown_export_error", error=str(oe))
                st.success("Analysis complete — review **Deliverables** below.")
                st.warning(f"Could not write review Markdown ({oe}). Check **SKYLINE_REVIEW_DIR**.")

        except Exception as e:
            log_event("pipeline_error", error=str(e))
            st.exception(e)

# --- Results ---
if st.session_state.last_grok:
    st.markdown("##### Deliverables")
    grok = st.session_state.last_grok
    _ps = (grok.get("primary_state") or "").strip()
    st.caption(
        f"**Primary state (for `skyline_review` subfolder):** `{_ps or '_unspecified'}` — "
        "operator-locked when you picked **Project state**; otherwise model-inferred."
    )
    tab_analysis, tab_draft, tab_cites, tab_technical = st.tabs(
        ["Analysis", "Draft", "Citations", "Technical"]
    )

    with tab_analysis:
        st.markdown(grok.get("analysis", "") or "_No analysis returned._")

    with tab_draft:
        st.text_area(
            "Editable draft",
            height=360,
            key="draft_preview",
            help="This text is sent when you choose Create Gmail draft.",
        )
        st.download_button(
            label="Download draft (.txt)",
            data=(st.session_state.get("draft_preview") or "").encode("utf-8"),
            file_name="elite_business_counsel_draft.txt",
            mime="text/plain",
            key="download_draft_txt",
            use_container_width=True,
        )

    with tab_cites:
        cites = grok.get("citations") or []
        if cites:
            for c in cites:
                st.write(f"- {c}")
        else:
            st.caption("No citations returned.")

    with tab_technical:
        st.caption("Grok pipeline metadata.")
        st.json(
            {
                "primary_state": grok.get("primary_state") or "",
                "note": "Empty string → files under SKYLINE_REVIEW_DIR/_unspecified/",
            }
        )
        st.caption("Structured evidence payload (for debugging or export).")
        st.code(
            merge_evidence_json(st.session_state.last_evidence_items),
            language="json",
        )

if draft_btn:
    body = (st.session_state.get("draft_preview") or "").strip()
    if not st.session_state.last_grok or not body:
        st.warning("Run **Analyze & draft** first and ensure the **Draft** tab contains text.")
    else:
        try:
            proofs = [
                p
                for p in st.session_state.last_evidence_paths
                if p and os.path.isfile(p)
            ]
            with st.spinner("Creating Gmail draft…"):
                service = get_gmail_service()
                info = create_gmail_draft(
                    service,
                    body,
                    thread_id.strip() or None,
                    proof_paths=proofs,
                    subject_override=draft_subject.strip() or None,
                )
            st.success(
                f"Draft saved in Gmail (folder **Drafts**, label **Dispute Draft**). "
                f"Draft ID: `{info['draft_id']}`"
            )
        except Exception as e:
            log_event("draft_create_error", error=str(e))
            st.exception(e)

# --- Deep admin (collapsed) ---
with st.expander("Administrator · connectivity & credentials", expanded=False):
    st.caption(f"Project root: `{ROOT}`")
    if ROOT.resolve() != INTENDED_PROJECT_ROOT.resolve():
        st.warning(
            f"Active build should live only at **`{INTENDED_PROJECT_ROOT}`**. "
            "Open that folder in Cursor and run Streamlit there so credentials and token stay in one place."
        )
    st.markdown(
        "| Check | Status |\n| --- | --- |\n"
        f"| credentials.json | {'OK' if cred_ok else 'Missing'} |\n"
        f"| token.pickle | {'OK' if tok_ok else 'Run `py oauth_login.py`'} |\n"
        f"| XAI_API_KEY | {'OK' if xai_ok else 'Missing'} |\n"
        f"| OCR key | {'OK' if ocr_ok else 'Optional'} |\n"
        f"| SKYLINE_REVIEW_DIR | `{SKYLINE_REVIEW_DIR}` (subfolders `CO`, `FL`, … or `_unspecified`) |\n"
    )
    if st.session_state.pop("secrets_just_saved", False):
        st.success("Secrets saved to this project folder.")

    if st.button("Run setup check", key="verify_setup_btn"):
        status = run_checks()
        st.code("\n".join(status.lines), language=None)

    st.subheader("Store secrets")
    st.caption("Writes to `.env` and optionally `credentials.json`. Data is sent to xAI / Google only when you run analysis or drafts.")
    xai_in = st.text_input("XAI_API_KEY (Grok)", type="password", key="store_xai")
    zhipu_in = st.text_input(
        "ZHIPU_API_KEY (OCR, optional)", type="password", key="store_zhipu"
    )
    creds_up = st.file_uploader(
        "Gmail OAuth JSON (Desktop client)",
        type=["json"],
        key="store_creds_json",
    )
    if st.button("Save to project folder", key="save_secrets_btn"):
        try:
            msgs = []
            keys_written = save_api_keys_to_dotenv(
                ROOT, xai_api_key=xai_in or None, zhipu_api_key=zhipu_in or None
            )
            if keys_written:
                msgs.append("Updated: " + ", ".join(keys_written) + " in .env")
            if creds_up is not None:
                save_gmail_credentials_json(ROOT, creds_up.getvalue())
                msgs.append("Saved credentials.json")
            if not msgs:
                st.warning("Enter at least one key or upload credentials.json.")
            else:
                load_dotenv(ROOT / ".env", override=True)
                st.session_state.secrets_just_saved = True
                st.rerun()
        except Exception as e:
            st.error(str(e))

    st.markdown(
        f"- Manual: edit `.env` or place files in `{ROOT}`\n"
        f"- Template: `SECRETS_TEMPLATE.txt` · Log: `{LOG_FILE.name}`"
    )

    with st.expander("Dedicated inbox & sync (optional)", expanded=False):
        st.markdown(
            "Set **`AGENT_GMAIL_ADDRESS`** and **`CORRESPONDENCE_ARCHIVE_DIR`** in `.env`, then run "
            "`py sync_worker.py` or `py sync_worker.py --once`.\n\n"
            "Optional Supabase: **`SUPABASE_URL`**, **`SUPABASE_SERVICE_ROLE_KEY`**, and **`supabase_schema.sql`**."
        )
        st.caption(
            "Shipped today: polling sync only (no Gmail push alerts). Supabase stores thread metadata and "
            "review-export audit rows—no vectors or semantic search. Retention and deletion stay manual unless "
            "counsel approves a written policy."
        )
