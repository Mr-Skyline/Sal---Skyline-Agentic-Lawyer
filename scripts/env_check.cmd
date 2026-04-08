@echo off
cd /d "%~dp0.."
set "ROOT=%CD%"
if exist "%ROOT%\.venv\Scripts\python.exe" (
  "%ROOT%\.venv\Scripts\python.exe" "%ROOT%\env_check.py"
) else (
  py "%ROOT%\env_check.py"
)
exit /b %ERRORLEVEL%
