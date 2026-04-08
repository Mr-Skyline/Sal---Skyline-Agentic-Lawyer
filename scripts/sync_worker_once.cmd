@echo off
REM Single sync_worker poll cycle (Task Scheduler friendly). Repository root = parent of scripts/.
REM See OPERATIONS_ELITE.txt section 3 — Windows Task Scheduler (arguments + Start in).
cd /d "%~dp0.."
set "ROOT=%CD%"
if exist "%ROOT%\.venv\Scripts\python.exe" (
  "%ROOT%\.venv\Scripts\python.exe" "%ROOT%\sync_worker.py" --once
) else (
  py "%ROOT%\sync_worker.py" --once
)
exit /b %ERRORLEVEL%
