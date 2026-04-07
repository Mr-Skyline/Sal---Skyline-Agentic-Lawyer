# Skyline / Sal build — living review checklist

Use this during implementation passes. Update dates and notes as releases ship.

**Last reviewed:** 2026-04-07

---

## Canonical project root (this machine)

**`C:\Users\travi\Projects\AI Lawyer Build`** is the **only** project tree for this build. Run Streamlit, `oauth_login.py`, `sync_worker.py`, and `verify_setup.py` from that folder so `credentials.json`, `token.pickle`, `.env`, and `SKYLINE_REVIEW_DIR` stay consistent. Do **not** maintain a second working copy elsewhere — duplicate folders break paths, OAuth, and Git. The same path is `INTENDED_PROJECT_ROOT` in `config.py` (for `verify_setup` warnings).

---

## Sidekick split (same prompt, two agents)

Use this so parallel work does not collide.

| **Build Sidekick #1** | **Build Sidekick #2** |
|------------------------|-------------------------|
| Python: `main.py`, `review_export.py`, `evidence.py`, `analysis.py`, `draft.py`, `gmail_retry.py` | `verify_setup.py`, `.env.example`, `SECRETS_TEMPLATE.txt`, `OAUTH_*.txt`, `run.cmd` |
| Supabase / `sync_worker.py` / `ingest.py` when touching data path | **Only** edit and run under `C:\Users\travi\Projects\AI Lawyer Build` — no parallel “second repo” |
| Tests / smoke imports | `docs/SKYLINE_BUILD_REVIEW.md` checkbox + **Last reviewed** date |

**Rule:** One sidekick per file per turn; if both need `main.py`, sequence or hand off to the primary agent.

**Multi-agent (broader than this table):** Procedures, lanes, and **Sal ownership** when delegated elsewhere → **`AGENT_TEAM_CHECKLIST.md`** and **`AGENTS.md`**.

---

## Each review pass (quick)

1. **Model vs code:** Does Sal claim Supabase writes, vectors, proactive scans, or auto-delete? → Must match what the current release actually does.
2. **Deadlines:** Any new “calendar math” in product copy or prompts → counsel review for CO, FL, AZ, TX, NE as applicable.
3. **Single project root:** `C:\Users\travi\Projects\AI Lawyer Build` only — same folder for `credentials.json`, `token.pickle`, `.env`, `SKYLINE_REVIEW_DIR`.
4. **Secrets:** Nothing sensitive in logs, Streamlit echo, or committed files (see `.gitignore`).
5. **PII mode:** Document whether UI is “internal” (full detail) vs “export” (redacted).

---

## Phase alignment (from plan)

| Track | Intent | Status |
|--------|--------|--------|
| A | Sal prompt + `SKYLINE_REVIEW_DIR` markdown output wired from app | Done (`sal_prompt` + `review_export.export_analysis_markdown`, naming expander, evidence excerpt; operator **Project state** lock + Technical metadata; prompt file vs deployed behavior per review pass 1) |
| B | Gmail/thread ingest (existing pipeline extended) | Partial (Streamlit evidence: `GMAIL_EVIDENCE_*` tunables + query description hints; core thread path; optional **Project state** lock for review subfolders) |
| C | Supabase metadata only | Partial (`db.py` thread upsert + `skyline_review_exports` insert audit; graceful skip on API/schema errors; `py verify_setup.py --supabase-ping`; `supabase_schema.sql` ops header + RLS note for future client exposure) |
| D | Embeddings + pattern search | TBD — design only: **`TRACK_D_EMBEDDINGS_DESIGN.md`** (no prod vectors / embedding calls until approved) |
| E | Worker: proactive / scheduled | Partial (polling `sync_worker.py`; `--once` + `sync_worker_once.cmd` for Task Scheduler; `--dry-run` + `preview_sync_cc_threads` listing; disk archive + state; **not** Gmail Pub/Sub or push-based proactive) |
| F | UI polish (black/gold, streamlined) | Deferred |

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

- **Product (code, UI, Sal prompts):** May present user-supplied or retrieved text and general educational language. Avoid encoding **jurisdiction-specific deadline math**, mandatory “file by” automation, or **auto-delete** of matter files unless counsel has approved a written spec. New calendar or deadline copy → “Each review pass” item 2 and update counsel checklists when signed off.
- **Counsel-owned:** Formal cheat sheets, retention policy, and approval for how hard-line statutory rules appear in assistant narrative for real matters.

---

## Handoff — open questions for Agents 1–2

| Topic | Question |
|-------|----------|
| Track D | Confirm v1 embedding **sources** (Gmail archive only vs include `skyline_review/*.md`) and whether vectors stay in **Supabase pgvector** vs external store. |
| Track D | If Sal uses retrieval: **RAG** contract (what gets injected into Grok) vs **standalone search UI** only for phase 1. |
| Track C | Any new tables or columns before Track D (e.g. storing normalized message text in DB) — coordinate with schema comments in `supabase_schema.sql`. |
| Model vs code | After each Sal prompt edit, skim review pass 1 so prompts still **disclaim** vectors / proactive features that are not shipped. |

---

## Notes

- **Python / pip:** Core deps in `requirements.txt` (3.11–3.12 recommended on Windows). OCR → `requirements-ocr.txt`; Supabase → `requirements-supabase.txt`; both → `requirements-full.txt`. `bootstrap_venv.cmd` prefers 3.12/3.11.
- **PII mode:** Streamlit + `skyline_review/*.md` exports are **internal** (full intake text and evidence excerpt in the file). Redact before external share.
- Prompt source of truth: `Skyline Lawyer – Full System Prompt.txt` (v2.1+).
- Re-run `py verify_setup.py` and `py verify_setup.py --strict` from **`C:\Users\travi\Projects\AI Lawyer Build`** after env changes; optional `py verify_setup.py --supabase-ping` when Supabase is configured.
- **Agent coordination:** `AGENT_TEAM_CHECKLIST.md` (living playbook), `AGENTS.md` (entry), `.cursor/rules/agent-team-checklist.mdc`.
- **Quick smoke:** `py smoke_check.py` (or `.venv\Scripts\python.exe smoke_check.py`) for fast module imports after dependency churn.
- **Track D design:** `TRACK_D_EMBEDDINGS_DESIGN.md`
- **Operator runbook:** `docs/OPERATIONS_ELITE.txt` — first-run order, quick failure index, shipped vs roadmap (keeps Sal/UI claims aligned with releases).
