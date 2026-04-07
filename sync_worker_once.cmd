@echo off
REM Single sync_worker poll cycle (Task Scheduler friendly). Canonical folder only.
REM See docs/OPERATIONS_ELITE.txt section 3 — Windows Task Scheduler (arguments + Start in).
cd /d "%~dp0"
if exist "%~dp0.venv\Scripts\python.exe" (
  "%~dp0.venv\Scripts\python.exe" "%~dp0sync_worker.py" --once
) else (
  py "%~dp0sync_worker.py" --once
)
exit /b %ERRORLEVEL%
