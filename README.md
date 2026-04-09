# Sal — Skyline Agentic Lawyer

[![CI](https://github.com/Mr-Skyline/Sal---Skyline-Agentic-Lawyer/actions/workflows/ci.yml/badge.svg)](https://github.com/Mr-Skyline/Sal---Skyline-Agentic-Lawyer/actions/workflows/ci.yml)

AI-powered legal sidekick for Skyline Painting: Gmail evidence ingestion, Grok-assisted dispute analysis, contract review, professional draft generation, Markdown audit trails, and optional Supabase logging.

**This software does not provide legal advice.** It assists with drafting and organization only.

---

## Project structure

```
.
├── main.py                  # Streamlit entry point
├── src/sal/                 # Core Python package
│   ├── analysis.py          # Grok (xAI) analysis + draft generation
│   ├── config.py            # Paths, API endpoints, constants
│   ├── sal_prompt.py        # Sal behavioral prompt loader
│   ├── evidence.py          # Gmail search, OCR, document parsing
│   ├── draft.py             # Gmail draft creation with MIME + labels
│   ├── review_export.py     # Markdown audit trail export
│   ├── db.py                # Optional Supabase persistence
│   ├── ingest.py            # Thread ingestion for sync worker
│   ├── sync_worker.py       # Continuous Gmail polling worker
│   ├── gmail_retry.py       # Exponential backoff for Gmail API
│   ├── logger_util.py       # JSONL append-only logging
│   ├── secrets_store.py     # Write API keys to .env
│   └── verify_setup.py      # Local setup checker
├── prompts/                 # Sal system prompt file
├── docs/                    # Build review, operations, OAuth guides, schema
├── scripts/                 # CLI tools, batch files, setup helpers
├── config/                  # .env.example, .streamlit theme, pytest config
├── tests/                   # Unit tests (pytest)
├── requirements.txt         # Core dependencies
├── requirements-dev.txt     # Dev/CI (pytest)
├── requirements-ocr.txt     # Optional OCR (GLM-OCR)
├── requirements-supabase.txt# Optional Supabase
└── requirements-full.txt    # All of the above
```

## Quick setup

1. **Python 3.11–3.12** recommended. Create a virtual environment:
   ```
   python -m venv .venv
   pip install -r requirements.txt
   ```

2. **Secrets:** Copy `.env.example` → `.env` and set at least `XAI_API_KEY`.

3. **Gmail:** Add Google OAuth Desktop client JSON as `credentials.json` at the project root, then:
   ```
   python scripts/oauth_login.py
   ```

4. **Run:**
   ```
   python -m streamlit run main.py
   ```

## Development

The **Makefile** is the primary shortcut for common tasks (after `pip install -r requirements-dev.txt`):

| Command | Purpose |
| --- | --- |
| `make test` | Run the full pytest suite (`python3 -m pytest tests/ -v`) |
| `make lint` | Run Ruff on `src/`, `tests/`, and `main.py` |
| `make smoke` | Quick import smoke check (`python3 scripts/smoke_check.py`) |

## Tests

```
pip install -r requirements-dev.txt
pytest
```

All tests live under `tests/`. No live API calls required.

## Docker

Build and run with Docker Compose:

```bash
docker compose up -d
```

This starts both the Streamlit UI (port 8501) and the sync worker. Place `.env`, `credentials.json`, and `token.pickle` in the project root before starting.

Build just the image:

```bash
docker build -t sal-skyline .
docker run -p 8501:8501 --env-file .env sal-skyline
```

## Key documentation

| Document | Location |
|---|---|
| Build review & phase alignment | `docs/SKYLINE_BUILD_REVIEW.md` |
| Operations runbook | `docs/OPERATIONS_ELITE.txt` |
| Supabase schema | `docs/supabase_schema.sql` |
| Secrets template | `docs/SECRETS_TEMPLATE.txt` |
| OAuth setup guides | `docs/OAUTH_STEPS.txt`, `docs/OAUTH_FALLBACK_STEPS.txt` |
| Embeddings design (Track D) | `docs/TRACK_D_EMBEDDINGS_DESIGN.md` |
| Agent coordination | `AGENT_TEAM_CHECKLIST.md`, `AGENTS.md` |

## Do not commit

`.env`, `credentials.json`, `token.pickle`, `.venv/`, `skyline_review/`, and logs are in `.gitignore`.

## Remote

[Mr-Skyline/Sal---Skyline-Agentic-Lawyer](https://github.com/Mr-Skyline/Sal---Skyline-Agentic-Lawyer)
