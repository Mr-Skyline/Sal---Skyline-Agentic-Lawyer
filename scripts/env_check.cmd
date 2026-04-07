@echo off
cd /d "%~dp0"
if exist "%~dp0.venv\Scripts\python.exe" (
  "%~dp0.venv\Scripts\python.exe" "%~dp0env_check.py"
) else (
  py "%~dp0env_check.py"
)
exit /b %ERRORLEVEL%
