@echo off
setlocal
cd /d "%~dp0"

REM Prefer 3.12 then 3.11 (reliable wheels on Windows). Avoid defaulting to 3.14 for fresh venvs.
py -3.12 -m venv .venv 2>nul
if exist ".venv\Scripts\python.exe" goto have_venv
py -3.11 -m venv .venv 2>nul
if exist ".venv\Scripts\python.exe" goto have_venv
py -m venv .venv

if not exist ".venv\Scripts\python.exe" (
  echo Could not create .venv. Install Python 3.12 from https://www.python.org/downloads/ and ensure the `py` launcher lists it.
  exit /b 1
)

:have_venv
echo Upgrading pip and installing core requirements...
".venv\Scripts\python.exe" -m pip install -U pip
".venv\Scripts\pip.exe" install -r "%~dp0requirements.txt"
echo.
echo Core install done. Optional: .venv\Scripts\pip.exe install -r requirements-ocr.txt
echo              and/or .venv\Scripts\pip.exe install -r requirements-supabase.txt
echo              or use requirements-full.txt for both extras.
exit /b 0
