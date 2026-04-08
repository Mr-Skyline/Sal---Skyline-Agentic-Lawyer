@echo off
setlocal
cd /d "%~dp0.."
set "ROOT=%CD%"

REM Prefer 3.12 then 3.11 (reliable wheels on Windows). Avoid defaulting to 3.14 for fresh venvs.
py -3.12 -m venv "%ROOT%\.venv" 2>nul
if exist "%ROOT%\.venv\Scripts\python.exe" goto have_venv
py -3.11 -m venv "%ROOT%\.venv" 2>nul
if exist "%ROOT%\.venv\Scripts\python.exe" goto have_venv
py -m venv "%ROOT%\.venv"

if not exist "%ROOT%\.venv\Scripts\python.exe" (
  echo Could not create .venv. Install Python 3.12 from https://www.python.org/downloads/ and ensure the `py` launcher lists it.
  exit /b 1
)

:have_venv
echo Upgrading pip and installing core requirements...
"%ROOT%\.venv\Scripts\python.exe" -m pip install -U pip
"%ROOT%\.venv\Scripts\pip.exe" install -r "%ROOT%\requirements.txt"
echo.
echo Core install done. Optional: "%ROOT%\.venv\Scripts\pip.exe" install -r "%ROOT%\requirements-ocr.txt"
echo              and/or "%ROOT%\.venv\Scripts\pip.exe" install -r "%ROOT%\requirements-supabase.txt"
echo              or use requirements-full.txt for both extras.
echo Optional: pip install -e "%ROOT%" for editable package and console scripts.
exit /b 0
