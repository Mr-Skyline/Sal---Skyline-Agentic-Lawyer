@echo off
REM Elite Business Counsel — launches Streamlit from the repository root (parent of scripts/).
REM Use one checkout only for credentials, .env, and token (see README).
setlocal
cd /d "%~dp0.."
set "ROOT=%CD%"

if exist "%ROOT%\.venv\Scripts\python.exe" (
  "%ROOT%\.venv\Scripts\python.exe" -m streamlit run "%ROOT%\main.py"
  exit /b %errorlevel%
)

py -3.12 -m streamlit run "%ROOT%\main.py" 2>nul
if %errorlevel% equ 0 exit /b 0

py -3.11 -m streamlit run "%ROOT%\main.py" 2>nul
if %errorlevel% equ 0 exit /b 0

py -m streamlit run "%ROOT%\main.py" 2>nul
if %errorlevel% equ 0 exit /b 0

py -3 -m streamlit run "%ROOT%\main.py"
exit /b %errorlevel%
