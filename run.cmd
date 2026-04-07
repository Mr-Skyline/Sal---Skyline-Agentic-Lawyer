@echo off
REM Elite Business Counsel — launches Streamlit from this script's folder.
REM ONLY active build location: C:\Users\travi\Projects\AI Lawyer Build
REM Do not use a second project copy for day-to-day work — this folder is the only tree.
setlocal
cd /d "%~dp0"

if exist "%~dp0.venv\Scripts\python.exe" (
  "%~dp0.venv\Scripts\python.exe" -m streamlit run "%~dp0main.py"
  exit /b %errorlevel%
)

REM Match bootstrap_venv.cmd: prefer 3.12 / 3.11 before whatever `py` defaults to.
py -3.12 -m streamlit run "%~dp0main.py" 2>nul
if %errorlevel% equ 0 exit /b 0

py -3.11 -m streamlit run "%~dp0main.py" 2>nul
if %errorlevel% equ 0 exit /b 0

py -m streamlit run "%~dp0main.py" 2>nul
if %errorlevel% equ 0 exit /b 0

py -3 -m streamlit run "%~dp0main.py"
exit /b %errorlevel%
