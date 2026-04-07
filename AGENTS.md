# Agents

## Before anything else

1. Read **AGENT_TEAM_CHECKLIST.md** (full file, or headers + **§2 Lanes** + **§7 Changelog** if timeboxed).
2. Obey the rules under `.cursor/rules/` — especially `agent-team-checklist.mdc` and `agent-autonomy.mdc`.

## Responsibilities

- **Lanes:** When parent + subagents or multiple agents could overlap, follow checklist **§2** (claim a lane, no duplicate research/edits).
- **Living doc:** Add durable operational steps to **AGENT_TEAM_CHECKLIST.md** and append a row to **§7 Changelog** when you do.
- **Handoff:** If you stop mid-task, use the **handoff block** in checklist **§6**.
- **Sal / Grok persona work:** When the user assigns **Sal** (prompt file, `sal_prompt.py`, Sal-related `analysis.py`) to **another agent**, stay out of that lane unless they explicitly move it here; keep the **checklist** current when team process changes.
- **Release checklist:** After substantive product changes, align **`SKYLINE_BUILD_REVIEW.md`** (review pass + **Last reviewed**) with what the code actually does.

## Where things live


| What                       | Where                                     |
| -------------------------- | ----------------------------------------- |
| Full playbook              | `AGENT_TEAM_CHECKLIST.md`                 |
| Release / phase alignment  | `SKYLINE_BUILD_REVIEW.md`                 |
| Ops runbook (first run + troubleshooting) | `OPERATIONS_ELITE.txt`     |
| Cursor enforcement         | `.cursor/rules/agent-team-checklist.mdc`  |
| Execution / secrets policy | `.cursor/rules/agent-autonomy.mdc`        |
| Agent docs ↔ canonical stack | `mirror_agent_docs.cmd` (see checklist **§3**) |
| PR merge-ready loop        | User **babysit** skill (see checklist §2) |


This file stays short; **AGENT_TEAM_CHECKLIST.md** is the source of truth for procedures.

## Cursor Cloud specific instructions

### Environment

- Python **3.12** virtual environment at `.venv/`. Activate: `source .venv/bin/activate`.
- Core + dev deps: `pip install -r requirements-dev.txt` (includes `requirements.txt` + `pytest`).
- `.env` must exist in the project root (copy from `.env.example`). At minimum set `XAI_API_KEY` (even a placeholder) so `verify_setup.py` passes without `--strict`.
- On Ubuntu/Debian the `python3.12-venv` system package is required to create the venv.

### Running services

- **Streamlit UI:** `streamlit run main.py --server.headless true --server.port 8501` — the app starts even without `credentials.json` / `token.pickle`; those are only needed for live Gmail operations.
- The `INTENDED_PROJECT_ROOT` warning ("not canonical root") is expected in Cloud Agent VMs — it can be ignored.

### Checks & tests

- `python smoke_check.py` — fast import sweep, no network calls.
- `python verify_setup.py` — environment diagnostics (non-strict passes without Gmail creds).
- `pytest` — **currently fails** with `ImportError` because `tests/test_analysis_json.py` and `tests/test_friendly_sal_api.py` import functions (`_normalize_sal_fields`, `_parse_sal_response_json`, `friendly_sal_api_message`) that do not exist in `analysis.py`. This is a pre-existing codebase issue, not an environment problem.

### Gotchas

- The `.cmd` / `.ps1` scripts in the repo are Windows-only; use the Linux equivalents above.
- Gmail OAuth (`oauth_login.py`) requires a browser and `credentials.json` from Google Cloud Console — this cannot be completed in headless Cloud Agent VMs. The Streamlit UI still loads and shows alerts for missing credentials.
- Optional extras: `requirements-ocr.txt` (ZHIPU OCR), `requirements-supabase.txt` (metadata DB). Neither is needed for core dev/testing.