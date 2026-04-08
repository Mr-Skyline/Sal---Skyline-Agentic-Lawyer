@echo off
REM Sal — Skyline Agentic Lawyer: launches Streamlit from the project root.
REM Run from project root: scripts\run.cmd
setlocal
cd /d "%~dp0.."

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m streamlit run main.py
  exit /b %errorlevel%
)

py -3.12 -m streamlit run main.py 2>nul
if %errorlevel% equ 0 exit /b 0

py -3.11 -m streamlit run main.py 2>nul
if %errorlevel% equ 0 exit /b 0

py -m streamlit run main.py 2>nul
if %errorlevel% equ 0 exit /b 0

py -3 -m streamlit run main.py
exit /b %errorlevel%
