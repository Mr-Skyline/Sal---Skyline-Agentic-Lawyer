@echo off
REM Single sync_worker poll cycle (Task Scheduler friendly).
REM See docs/OPERATIONS_ELITE.txt for Task Scheduler setup.
cd /d "%~dp0.."
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m src.sal.sync_worker --once
) else (
  py -m src.sal.sync_worker --once
)
exit /b %ERRORLEVEL%
