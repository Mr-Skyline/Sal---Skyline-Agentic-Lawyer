# Repository structure

## Root

| File | Purpose |
|---|---|
| `main.py` | Streamlit UI entry point — matter intake, evidence retrieval, Grok analysis, draft creation |
| `README.md` | Quick setup and overview |
| `STRUCTURE.md` | This file |
| `AGENTS.md` | Agent coordination entry point |
| `AGENT_TEAM_CHECKLIST.md` | Living playbook for multi-agent workflow |
| `.env.example` | Template for local secrets (copy to `.env`) |
| `requirements*.txt` | Dependency manifests (core, dev, OCR, Supabase, full) |
| `pyproject.toml` | PEP 621 project metadata, dependencies, entry points, tool config (includes `[tool.pytest.ini_options]`) |
| `.gitignore` | Secrets, venv, caches, local archives |
| `.python-version` | Preferred Python version (pyenv) |

## `src/sal/` — Core package

All application logic lives here as a proper Python package with relative imports.

| Module | Responsibility |
|---|---|
| `__main__.py` | Package entry: `python -m src.sal` runs the sync worker (`sync_worker.main`) |
| `config.py` | Paths, env vars, API endpoints, state codes, constants |
| `analysis.py` | Grok chat completion, JSON response parsing, error formatting |
| `sal_prompt.py` | Load Sal behavioral text from prompt file, JSON contract suffix |
| `evidence.py` | Gmail OAuth, message search/fetch, OCR, document parsing, merge |
| `draft.py` | Gmail draft creation with MIME, reply threading, labels |
| `review_export.py` | Markdown audit trail under `SKYLINE_REVIEW_DIR/<state>/` |
| `db.py` | Optional Supabase: thread upsert + review audit insert |
| `ingest.py` | Thread discovery, JSON archiving, sync state management |
| `sync_worker.py` | Continuous/one-shot Gmail polling worker |
| `gmail_retry.py` | Exponential backoff wrapper for Gmail API calls |
| `logger_util.py` | Append-only JSONL event logging |
| `secrets_store.py` | Write API keys to `.env`, validate Gmail OAuth JSON |
| `verify_setup.py` | Environment checker (CLI + Streamlit callable) |

## `prompts/`

| File | Purpose |
|---|---|
| `Skyline Lawyer – Full System Prompt.txt` | Sal's behavioral instructions (through Phase 7) |

## `docs/`

| File | Purpose |
|---|---|
| `SKYLINE_BUILD_REVIEW.md` | Phase alignment, model-vs-code honesty, counsel sign-offs |
| `OPERATIONS_ELITE.txt` | First-run order, troubleshooting, Task Scheduler recipe |
| `supabase_schema.sql` | DDL for `correspondence_threads` + `skyline_review_exports` |
| `SECRETS_TEMPLATE.txt` | Blank secrets template |
| `TRACK_D_EMBEDDINGS_DESIGN.md` | Future embeddings / vector search design |
| `OAUTH_STEPS.txt` | OAuth setup walkthrough |
| `OAUTH_FALLBACK_STEPS.txt` | OAuth troubleshooting |
| `REDIRECT_URI_FIX.txt` | Redirect URI mismatch fixes |
| `CURSOR_AUTONOMY.txt` | Agent execution policy |

## `scripts/`

| File | Purpose |
|---|---|
| `run.cmd` | Launch Streamlit (Windows batch) |
| `oauth_login.py` | Gmail OAuth flow outside Streamlit |
| `oauth_diagnose.py` | Credentials.json inspector |
| `oauth_google_checklist.py` | Google Cloud redirect URI printer |
| `print_redirect_uri.py` | Quick redirect URI list |
| `env_check.py` | Grok/Sal environment sanity check |
| `smoke_check.py` | Fast import smoke test |
| `ensure_correspondence_archive.py` | Create archive dir + update .env |
| `bootstrap_venv.cmd` | Create .venv with correct Python version |
| `sync_worker_once.cmd` | Run sync_worker --once (Task Scheduler) |
| `env_check.cmd` / `EnvCheck.ps1` | Environment check wrappers |
| `mirror_agent_docs.cmd` | Doc sync utility |
| `PUSH_NOW.ps1` | Git push helper |
| `init_for_github.ps1` | Initial GitHub setup |

## `tests/`

| File | Purpose |
|---|---|
| `test_analysis_json.py` | JSON parsing + field normalization tests |
| `test_friendly_sal_api.py` | Operator-facing error message tests |
