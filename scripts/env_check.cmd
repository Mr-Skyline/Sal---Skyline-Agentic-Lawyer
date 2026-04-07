@echo off
cd /d "%~dp0.."
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" scripts\env_check.py
) else (
  py scripts\env_check.py
)
exit /b %ERRORLEVEL%
