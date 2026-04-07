# Sal · Skyline Lawyer

Streamlit workspace for Skyline Painting: Gmail evidence, **Sal** (Grok) analysis and drafting, Markdown review export, optional Gmail draft creation.

This software **does not provide legal advice**. It assists with drafting and organization only.

## Where this project lives

Intended active root (also `INTENDED_PROJECT_ROOT` in `config.py`):

`C:\Users\travi\Projects\AI Lawyer Build`

Open Cursor and terminals there. Run `py verify_setup.py` from this folder.

## Quick setup

1. **Python:** 3.11–3.12 recommended; create `.venv` and `pip install -r requirements.txt` (optional: `requirements-ocr.txt`, `requirements-supabase.txt`).
2. **Secrets:** copy `.env.example` → `.env`; set at least `XAI_API_KEY`.
3. **Gmail:** add Google OAuth **Desktop** client JSON as `credentials.json`, then `py oauth_login.py`.
4. **Run:** `py -m streamlit run main.py`

More detail: **`OPERATIONS_ELITE.txt`**, build checklist: **`SKYLINE_BUILD_REVIEW.md`**.

## Tests

From the project root (with `.venv` activated if you use one):

```powershell
pip install -r requirements-dev.txt
pytest
```

Tests live under **`tests/`** (Sal JSON parsing and friendly API error strings; no live Grok calls).

## GitHub

Remote: [Mr-Skyline/Sal---Skyline-Agentic-Lawyer](https://github.com/Mr-Skyline/Sal---Skyline-Agentic-Lawyer)

After Git is installed and `git config --global user.name` / `user.email` are set:

```powershell
Set-Location "C:\Users\travi\Projects\AI Lawyer Build"
powershell -ExecutionPolicy Bypass -File .\PUSH_NOW.ps1
```

## Do not commit

`.env`, `credentials.json`, `token.pickle`, `.venv/`, `skyline_review/`, and logs are listed in `.gitignore`.

## Troubleshooting Git

**Do not** `git clone` the repo *into* this folder (you get a nested `Sal---Skyline-Agentic-Lawyer/` folder and Git records it wrong). This tree **is** the repo; use `git init` / `PUSH_NOW.ps1` here only.

If push is rejected because GitHub already has a README: run `git pull origin main --allow-unrelated-histories --no-rebase`, resolve any conflicts, then `git push -u origin main`.

**Replace placeholder identity:** `git config --global user.name` / `user.email` should be your real name and email, not the examples.
