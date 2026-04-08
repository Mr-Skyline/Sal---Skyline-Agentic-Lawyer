# Sal · Skyline Lawyer

Streamlit workspace for Skyline Painting: Gmail evidence, **Sal** (Grok) analysis and drafting, Markdown review export, optional Gmail draft creation.

This software **does not provide legal advice**. It assists with drafting and organization only.

## Where this project lives

Use **one** clone of this repository as your working tree. Open Cursor with **File → Open Folder** on the repo root, run every terminal and script from there, and do **not** keep a second working copy elsewhere (duplicate trees break OAuth paths, `.env`, and Git).

Optional: set **`INTENDED_PROJECT_ROOT`** in `.env` to the absolute path you treat as canonical; `verify_setup.py` warns if the current folder does not match (unset it to compare against the repo root only).

Run `py verify_setup.py` from the repo root.

## Quick setup

1. **Python:** 3.11–3.12 recommended; create `.venv`, then `pip install -r requirements.txt` **or** `pip install -e .` (installs the `sal` package from `pyproject.toml`). Optional extras: `pip install -e ".[ocr]"`, `pip install -e ".[supabase]"`, or the matching `requirements-*.txt` files.
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
Set-Location path\to\this\repo
powershell -ExecutionPolicy Bypass -File .\scripts\PUSH_NOW.ps1
```

Root stubs `PUSH_NOW.ps1` and `run.cmd` forward to `scripts\` for compatibility.

## Do not commit

`.env`, `credentials.json`, `token.pickle`, `.venv/`, `skyline_review/`, and logs are listed in `.gitignore`.

## Troubleshooting Git

**Do not** `git clone` the repo *into* this folder (you get a nested `Sal---Skyline-Agentic-Lawyer/` folder and Git records it wrong). This tree **is** the repo; use `git init` / `scripts\PUSH_NOW.ps1` (or the root stub) here only.

If push is rejected because GitHub already has a README: run `git pull origin main --allow-unrelated-histories --no-rebase`, resolve any conflicts, then `git push -u origin main`.

**Replace placeholder identity:** `git config --global user.name` / `user.email` should be your real name and email, not the examples.
