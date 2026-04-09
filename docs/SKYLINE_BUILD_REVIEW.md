# Skyline / Sal build — living review checklist

Use this during implementation passes. Update dates and notes as releases ship.

**Last reviewed:** 2026-04-09

---

## Canonical project root (this machine)

Run Streamlit, `scripts/oauth_login.py`, `src/sal/sync_worker.py`, and `src/sal/verify_setup.py` from the project root so `credentials.json`, `token.pickle`, `.env`, and `SKYLINE_REVIEW_DIR` stay consistent. Do **not** maintain a second working copy elsewhere. The canonical root is `INTENDED_PROJECT_ROOT` in `src/sal/config.py`.

---

## Sidekick split (same prompt, two agents)

Use this so parallel work does not collide.

| **Build Sidekick #1** | **Build Sidekick #2** |
|------------------------|-------------------------|
| Python: `main.py`, `src/sal/review_export.py`, `src/sal/evidence.py`, `src/sal/analysis.py`, `src/sal/draft.py`, `src/sal/gmail_retry.py` | `src/sal/verify_setup.py`, `.env.example`, `docs/SECRETS_TEMPLATE.txt`, `docs/OAUTH_*.txt`, `scripts/run.cmd` |
| Supabase / `src/sal/sync_worker.py` / `src/sal/ingest.py` when touching data path | **Only** edit and run under the project root — no parallel "second repo" |
| Tests / smoke imports | `docs/SKYLINE_BUILD_REVIEW.md` checkbox + **Last reviewed** date |

**Rule:** One sidekick per file per turn; if both need `main.py`, sequence or hand off to the primary agent.

**Multi-agent (broader than this table):** Procedures, lanes, and **Sal ownership** when delegated elsewhere → **`AGENT_TEAM_CHECKLIST.md`** and **`AGENTS.md`**.

---

## Each review pass (quick)

1. **Model vs code:** Does Sal claim Supabase writes, vectors, proactive scans, or auto-delete? → Must match what the current release actually does.
2. **Deadlines:** Any new "calendar math" in product copy or prompts → counsel review for CO, FL, AZ, TX, NE as applicable.
3. **Single project root:** Same folder for `credentials.json`, `token.pickle`, `.env`, `SKYLINE_REVIEW_DIR`.
4. **Secrets:** Nothing sensitive in logs, Streamlit echo, or committed files (see `.gitignore`).
5. **PII mode:** Document whether UI is "internal" (full detail) vs "export" (redacted).

---

## Phase alignment (from plan)

| Track | Intent | Status |
|--------|--------|--------|
| A | Sal prompt + `SKYLINE_REVIEW_DIR` markdown output wired from app | Done (`sal_prompt` + `review_export.export_analysis_markdown`, naming expander, evidence excerpt; operator **Project state** lock + Technical metadata; prompt file vs deployed behavior per review pass 1) |
| B | Gmail/thread ingest (existing pipeline extended) | Partial (Streamlit evidence: `GMAIL_EVIDENCE_*` tunables + query description hints; core thread path; optional **Project state** lock for review subfolders) |
| C | Supabase metadata only | Done (service role) — `src/sal/db.py` cached client + thread upsert + review audit insert + batch upsert + query functions; `docs/supabase_schema.sql` v1.0 with RLS policy templates, updated_at trigger; graceful skip on errors. Client-side RLS policies documented but commented until browser exposure. |
| D | Embeddings + pattern search | TBD — design only: **`docs/TRACK_D_EMBEDDINGS_DESIGN.md`** (no prod vectors / embedding calls until approved) |
| E | Worker: proactive / scheduled | Done for polling path (`src/sal/sync_worker.py`): SIGINT/SIGTERM graceful shutdown, exponential backoff, `--once` / `scripts/sync_worker_once.cmd`, `--dry-run` + `preview_sync_cc_threads`, disk archive + atomic state, **`--status`** + `correspondence_sync_state.health.json` for monitors, **`format_sync_summary`** + JSONL `sync_cycle_summary` for structured logs, JSONL size rotation via `SAL_LOG_JSONL_MAX_BYTES` in `logger_util.py`. **Still** polling-only — **not** Gmail Pub/Sub or push-based proactive. |
| F | UI polish (black/gold, streamlined) | Done (dark theme, gold button accents, Cormorant Garamond + Source Sans 3 typography, tab icons, enhanced sidebar status, citation formatting, footer) |

---

## Statute & retention

### Counsel-owned sign-offs (tracking only)

The checkboxes below are **workflow trackers** for licensed counsel review. They are not legal advice, and this repo does not encode statute-specific outcomes or filing deadlines as authoritative logic.

- [ ] Colorado lien cheat sheet signed off
- [ ] Florida Ch. 713 (NTO / claim timing) signed off
- [ ] Arizona 20-day + 33-993 completion signed off
- [ ] Texas Ch. 53 monthly notices + affidavit dates signed off
- [ ] Nebraska 120-day + service + residential notice signed off
- [ ] Written retention policy (no auto-delete of matter files without approval)

### Product vs counsel boundaries

- **Product (code, UI, Sal prompts):** May present user-supplied or retrieved text and general educational language. Avoid encoding **jurisdiction-specific deadline math**, mandatory "file by" automation, or **auto-delete** of matter files unless counsel has approved a written spec. New calendar or deadline copy → "Each review pass" item 2 and update counsel checklists when signed off.
- **Counsel-owned:** Formal cheat sheets, retention policy, and approval for how hard-line statutory rules appear in assistant narrative for real matters.

---

## Handoff — open questions for Agents 1–2

| Topic | Question |
|-------|----------|
| Track D | Confirm v1 embedding **sources** (Gmail archive only vs include `skyline_review/*.md`) and whether vectors stay in **Supabase pgvector** vs external store. |
| Track D | If Sal uses retrieval: **RAG** contract (what gets injected into Grok) vs **standalone search UI** only for phase 1. |
| Track C | Any new tables or columns before Track D (e.g. storing normalized message text in DB) — coordinate with schema comments in `docs/supabase_schema.sql`. |
| Model vs code | After each Sal prompt edit, skim review pass 1 so prompts still **disclaim** vectors / proactive features that are not shipped. |

---

## Notes

- **Python / pip:** Core deps in `requirements.txt` (3.11–3.12 recommended on Windows). OCR → `requirements-ocr.txt`; Supabase → `requirements-supabase.txt`; both → `requirements-full.txt`. `scripts/bootstrap_venv.cmd` prefers 3.12/3.11.
- **PII mode:** Streamlit + `skyline_review/*.md` exports are **internal** (full intake text and evidence excerpt in the file). Redact before external share.
- Prompt source of truth: `prompts/Skyline Lawyer – Full System Prompt.txt` (v2.1+).
- **Repo structure:** See `STRUCTURE.md` at the project root for a full file map.
- **Agent coordination:** `AGENT_TEAM_CHECKLIST.md` (living playbook), `AGENTS.md` (entry), `.cursor/rules/agent-team-checklist.mdc`.
- **Test coverage:** All 13 `src/sal/` modules have unit tests. Run `python -m pytest tests/ -v` from root.
- **Quick smoke:** `py scripts/smoke_check.py` for fast module imports after dependency churn.
- **Track D design:** `docs/TRACK_D_EMBEDDINGS_DESIGN.md`
- **Operator runbook:** `docs/OPERATIONS_ELITE.txt` — first-run order, quick failure index, shipped vs roadmap (keeps Sal/UI claims aligned with releases).
- **CI/CD:** GitHub Actions runs pytest on Python 3.11 + 3.12 on every push and PR. Ruff lint check included.
