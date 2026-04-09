# Agent team — operating checklist (living document)

**Status:** Mandatory pre-flight for every agent session or new task in this repo.

## How to use this file

1. **Before** writing code, running tools, or answering architecture questions, read this file top to bottom (or skim section headers + changelog at the bottom).
2. **After** you establish a new repeatable step (script, env var, pitfall, review gate), **add it** under the best-fitting section. Keep ordering: *before work → lanes → env → domain → during → handoff*. If a step is obsolete, strike through or remove it in the same edit and note why briefly.
3. Do **not** duplicate content across sections; link to one canonical bullet instead.

---

## 1. Before you proceed

- [ ] **Skim `AGENTS.md`** — one-page entry; this checklist is the detailed playbook.
- [ ] **Read this checklist** for the current task — including **§2 Lanes** if multiple agents or subagents are active.
- [ ] **Read project rules:** `.cursor/rules/*.mdc` (especially autonomy + team checklist rule).
- [ ] **Canonical project root:** active build is only `C:\Users\travi\Projects\AI Lawyer Build` (`INTENDED_PROJECT_ROOT` in `src/sal/config.py`). Open Cursor and terminals there. If you open a different folder, `python -m src.sal.verify_setup` warns — use one tree only unless you are explicitly reconciling copies.
- [ ] **Secrets:** never commit `.env`, `credentials.json`, or `token.pickle`; never paste API keys or tokens into chat or docs.
- [ ] **Windows Python:** do not assume `python` works. Prefer `.\.venv\Scripts\python.exe`, or `py -3.12` / `py -3.11`, then `py -3`. Use `bootstrap_venv.cmd` to create `.venv` if missing.
- [ ] **Scope:** only change what the task requires; match existing style and patterns in touched files.
- [ ] **Release / review doc:** When you change **model claims vs code**, **PII/export posture**, or **phase track status**, skim **`SKYLINE_BUILD_REVIEW.md`** (“Each review pass” + phase table). Bump **`Last reviewed`** when you complete that review pass for the same session of work.

## 2. Lanes, subagents, and avoiding overlap

**Goal:** Multiple agents (or parent + subagents) must not redo the same investigation, edit the same slice twice, or contradict each other’s in-flight work.

- [ ] **Know your role:** If you are a **subagent** (explore, shell, task runner, etc.), your job is to **return a tight summary** (findings, file paths, commands run, blockers). The **parent** agent merges that into the plan and applies code changes unless the user explicitly delegated implementation to you alone.
- [ ] **Claim a lane at the start:** In your first substantive reply for the task, be explicit: *what you are doing* and *what you are not redoing* (e.g. “Implementing `src/sal/analysis.py` only; not re-running Gmail OAuth.”).
- [ ] **Read before you research:** Skim the **current user message + recent thread** for another agent’s conclusions. If they already listed files or root cause, **build on it** — do not re-grep or re-read the whole repo from zero unless their output is wrong or incomplete.
- [ ] **Single writer per slice:** For a given file + feature, **one** agent should own edits per handoff. If you receive a handoff, note *files already modified* and continue from there instead of re-applying the same patch.
- [ ] **PR / CI / merge babysitting:** Treat **PR merge-readiness** (comments, conflicts, CI loops) as its own lane. Use the user’s **babysit** skill when that is the ask; do not mix large unrelated refactors into that pass unless the user asked for both.
- [ ] **No parallel duplicate tasks:** If the user launched two agents on the same ticket, **diff against reality**: check git status / open files / last message for what is already done before you implement.
- [ ] **Sal lane (when delegated elsewhere):** If the user says **another agent owns the Sal project** (prompt text, `src/sal/sal_prompt.py`, Sal/Grok wiring), **do not** re-implement or “fix” that slice here unless they explicitly route the task to you. **Do** keep **§7 Changelog** and related bullets accurate when their work changes how the team should run.
- [ ] **Roadmap & hygiene (Agent 3):** `docs/SKYLINE_BUILD_REVIEW.md`, `docs/TRACK_D_*.md`, `docs/OPERATIONS_ELITE.txt`, checklist changelog, `.env.example` / `docs/SECRETS_TEMPLATE.txt`, bootstrap/requirements notes — **not** feature logic in `main.py` / `src/sal/analysis.py` / `src/sal/sync_worker.py` / `src/sal/ingest.py` except **factual** operator copy or broken doc references.

## 3. Environment & diagnostics

- [ ] **Single workspace:** Open Cursor and terminals **only** under the project root (`INTENDED_PROJECT_ROOT` in `src/sal/config.py`). If you ever opened a different folder by mistake, **`scripts/mirror_agent_docs.cmd`** can copy agent docs; prefer fixing the workspace path instead of two trees.
- [ ] To verify Grok env loading without exposing the key: run `scripts/env_check.py` via `.venv\Scripts\python.exe` or `scripts/EnvCheck.ps1` / `scripts/env_check.cmd` from project root.
- [ ] Core deps: `requirements.txt`; OCR / Supabase: optional requirement files as documented in `scripts/bootstrap_venv.cmd` output.
- [ ] Optional env vars: see `.env.example` (`XAI_API_KEY`, `GROK_MODEL`, `GROK_MAX_OUTPUT_TOKENS`, `SAL_PROMPT_PATH`, Gmail/OAuth, Supabase, etc.).
- [ ] **Package structure:** All core Python lives in `src/sal/`. Entry point: `main.py`. Scripts: `scripts/`. Docs: `docs/`. Prompts: `prompts/`.
- [ ] **Docker:** From project root, `docker compose up -d` runs Streamlit (8501) + `sync-worker`; needs `.env`, `credentials.json`, and `token.pickle` at repo root (see `README.md` Docker section).

## 4. Application behavior (Skyline / Sal)

- [ ] **Owner:** Sal prompt + Grok integration may be maintained by **another agent** when the user says so; confirm in-thread before editing `prompts/Skyline Lawyer – Full System Prompt.txt`, `src/sal/sal_prompt.py`, or Sal-related paths in `src/sal/analysis.py`.
- [ ] Grok analysis uses **Sal** from `prompts/Skyline Lawyer – Full System Prompt.txt` (through Phase 7; Phase 8 stripped) via `sal_prompt.load_sal_behavioral_text`, plus `json_tool_contract_suffix` and `run_mode_suffix` in `src/sal/sal_prompt.py`; **`src/sal/analysis.py` composes** the system message and calls Grok. Override path with **`SAL_PROMPT_PATH`**. If the file is missing or empty, **`analysis.py` falls back** to inline `SYSTEM_PROMPT_DISPUTE` / `SYSTEM_PROMPT_BUSINESS`.
- [ ] `assistant_profile`: `dispute` vs `business_counsel` only adjusts a short run-mode add-on; same Sal core.
- [ ] `state_hint` / `primary_state` and review paths: `src/sal/config.py`, `src/sal/review_export.py`, `main.py`.
- [ ] **Non-Sal surfaces (reference):** Streamlit entry **`main.py`** / **`scripts/run.cmd`**; Gmail evidence **`src/sal/evidence.py`** + **`src/sal/draft.py`**; optional **`src/sal/sync_worker.py`** + **`src/sal/ingest.py`**; setup **`src/sal/verify_setup.py`**. Phase intent vs status: **`docs/SKYLINE_BUILD_REVIEW.md`** (not duplicated here).

## 5. While implementing

- [ ] Run linters / quick import checks on files you edit when available.
- [ ] Prefer **full commands** for user-facing instructions if the user works from a fresh shell (explicit `cd` to project root).
- [ ] Execute fixes in-terminal when the task allows; avoid “you should run X” without running X yourself unless blocked (e.g. user-only OAuth browser step).
- [ ] Optional: `py -m src.sal.verify_setup` or `py scripts/env_check.py` from project root when diagnosing environment issues.
- [ ] Quick import sweep: `py scripts/smoke_check.py` before a big merge or after dependency changes.
- [ ] Tests: `pytest` from project root (config in `pyproject.toml`).
- [ ] **`src/sal/db.py` + `lru_cache`:** `_cached_supabase_client` is keyed only by call args (none), not env — tests that vary `SUPABASE_*` must call `_cached_supabase_client.cache_clear()` or use the autouse fixture in `tests/test_db.py`.

## 6. Before you stop (handoff)

- [ ] **Handoff block for the next agent (required if work is partial):** *Done:* … · *Next:* … · *Files touched:* … · *Do not redo:* … · *Risks / open questions:* …
- [ ] Task goal met or explicit partial outcome documented for the next agent.
- [ ] If you added a **durable** operational step, **append it** to this checklist (or extend `.env.example` / scripts) in the same PR/session.
- [ ] **Changelog row** in §7: date (YYYY-MM-DD) + what you added or changed in the checklist.
- [ ] **Doc conflicts:** If this checklist and another repo doc disagree, prefer this file after a quick check against code, then fix the stale doc (or this checklist) in the same change.

---

## 7. Changelog (append only)


| Date       | Agent / note       | Change                                                                     |
| ---------- | ------------------ | -------------------------------------------------------------------------- |
| 2026-04-06 | Initial team setup | Created checklist + Cursor rule; Windows/Python and Sal pointers.          |
| 2026-04-06 | Lanes / overlap    | Added §2 subagent lanes, single-writer, babysit lane, handoff block in §6. |
| 2026-04-06 | Docs + health      | Expanded `AGENTS.md`; checklist cross-link + checkboxes + `verify_setup.py` bullet; review pass. |
| 2026-04-06 | Dual root          | Same `AGENTS.md`, checklist, and `.cursor/rules` must exist under **`C:\Users\travi\Projects\AI Lawyer Build`** when sidekicks use that workspace (not only OneDrive). |
| 2026-04-07 | Sidekick pass      | §1 canonical root clarified (Projects only, duplicate = verify warning); §6 doc-conflict rule; `AGENTS.md` links `SKYLINE_BUILD_REVIEW.md` + plain **bold** doc names. |
| 2026-04-07 | Stack sync         | Added `mirror_agent_docs.cmd` (push to Projects / `backup` pull) + §3 bullet. |
| 2026-04-07 | Sal + env check    | Added `sal_prompt.py`, wired `analysis.py` to Sal file + JSON contract; `env_check.py` / `.cmd` / `EnvCheck.ps1`; `.env.example` `GROK_MAX_OUTPUT_TOKENS` / `SAL_PROMPT_PATH`. |
| 2026-04-08 | Sal lane split       | User: other agents own Sal implementation; §2 + §4 ownership notes; `AGENTS.md` Sal lane bullet; this agent keeps checklist current. |
| 2026-04-09 | Checklist + release  | §1 `SKYLINE_BUILD_REVIEW.md` / Last reviewed; §4 non-Sal reference row; `SKYLINE_BUILD_REVIEW` Notes multi-agent pointer; `agent-team-checklist.mdc` Sal deferral. |
| 2026-04-09 | YOLO hygiene        | `verify_setup.py` ASCII Python note; added `smoke_check.py`; §5 smoke bullet. |
| 2026-04-10 | Agent 1 data plane  | `verify_setup --supabase-ping`; `db.py` upsert try/except; `sync_worker_once.cmd`; `OPERATIONS` disk vs DB; schema ops header; Track C/E in `SKYLINE_BUILD_REVIEW`. |
| 2026-04-11 | Phase 1 ops         | `OPERATIONS_ELITE.txt`: Task Scheduler recipe (cmd.exe + `sync_worker_once.cmd`), logs/troubleshooting, Supabase ping failure order. |
| 2026-04-09 | YOLO pass 2         | `env_check.py` ASCII-safe Sal path line; `sync_worker.py --dry-run`; `OPERATIONS_ELITE.txt` health + dry-run lines. |
| 2026-04-11 | Agent 3 roadmap     | `SKYLINE_BUILD_REVIEW.md`: phase A–E aligned to code, Last reviewed, Track D pointer; `TRACK_D_EMBEDDINGS_DESIGN.md`; statute/retention product vs counsel + handoff table for Agents 1–2. |
| 2026-04-11 | Agent 3 runbook     | `OPERATIONS_ELITE.txt`: first-run order, troubleshooting index, shipped vs roadmap; canonical `SKYLINE` note; `AGENTS.md` ops row; `main.py` caption under dedicated inbox (truth vs roadmap). |
| 2026-04-12 | Agent 3 playbook    | §2 Agent 3 lane; §3 `mirror_agent_docs` exclusions; §4 Sal stack wording (`load_sal_behavioral_text` + `sal_prompt` JSON/mode suffixes + `analysis.py` compose); `mirror_agent_docs.cmd` REM for non-mirrored files. |
| 2026-04-12 | Single project root   | User: **only** `C:\Users\travi\Projects\AI Lawyer Build`. README + `SKYLINE_BUILD_REVIEW` + `SECRETS_TEMPLATE` + `run.cmd` + `config` comment; §3 checklist = one workspace, mirror script recovery-only; deleted stray `Windows PowerShell*.txt` from repo root. |
| 2026-04-07 | Master Builder restructure | Full repo reorganization: `src/sal/` Python package, `docs/`, `scripts/`, `prompts/`, `config/`. Implemented `_parse_sal_response_json`, `_normalize_sal_fields`, `friendly_sal_api_message`. All 14 tests pass. Updated §3–§5 paths. |
| 2026-04-07 | Quality Inspector  | Security audit clean; model-vs-code verified; added tests/test_core_utils.py; docs/OPERATIONS_ELITE.txt paths updated. |
| 2026-04-08 | Round 2 integration | Track F partial; draft.py branding; SKYLINE_BUILD_REVIEW bumped to 2026-04-08. |
| 2026-04-08 | Round 3 grind | Full test coverage: all 13 src/sal/ modules tested; CI/CD pipeline; Makefile. |
| 2026-04-08 | Round 4 grind | review_export tests; Track D doc paths; CI note in build review. |
| 2026-04-07 | CI / tests            | `gh api …/actions/runs` can return empty `workflow_runs` if the token lacks **Actions read** or the repo has no workflows; pytest expected `analysis.py` helpers (`_parse_sal_response_json`, `_normalize_sal_fields`, `friendly_sal_api_message`) — implemented and wired `analyze_and_draft` to shared JSON path + empty-choices guard. |
| 2026-04-07 | CI workflow           | Added `.github/workflows/ci.yml`: Ubuntu, Python 3.11/3.12, `pip install -r requirements-dev.txt`, `pytest tests/`. `APITimeoutError` is a subclass of `APIConnectionError` in openai — check timeout before connection in `friendly_sal_api_message`. |
| 2026-04-08 | PR #2 merge main      | Resolved conflicts: CI combines `cursor/**` push triggers + pip cache + verbose pytest + import smoke; `src/sal/analysis.py` keeps brace JSON extract, merges `friendly_sal_api_message` chain + timeout-before-connection + single-quote string literals in `_extract_json_object`; `_normalize_sal_fields` handles missing `analysis` key. |
| 2026-04-08 | dotenv override       | `sync_worker.py` + `verify_setup.py`: `load_dotenv(..., override=False)` so subprocess/tests/Task Scheduler env is not clobbered by `.env`; `test_run_checks_no_xai_key` mocks `load_dotenv` when asserting missing `XAI_API_KEY`. |
| 2026-04-08 | Loose ends cleanup | Stale path refs + old branding fixed across AGENTS, checklist §1-§5, OPERATIONS header. |
| 2026-04-08 | Track E completion | sync_worker: health file, --status flag, structured summaries, format_sync_summary. |
| 2026-04-09 | Workflow Engineer | `db.py`: cached Supabase client, batch upsert, read helpers; `test_db.py` autouse `cache_clear` + no-Supabase tests; §5 lru_cache testing note. |
| 2026-04-08 | Option 3 hardening | Track C done: db.py cached client + batch + query; schema RLS templates + trigger; Docker containerization. |
| 2026-04-09 | Repo Architect Docker | Added `Dockerfile`, `docker-compose.yml`, `.dockerignore`; README Docker section; STRUCTURE.md rows; §3 Docker bullet. |
| 2026-04-09 | Track D v1 | Embeddings: chunking + embedding API + pgvector store + Streamlit search panel. All 6 tracks addressed. |
