@echo off
REM ============================================================
REM  Elite Business Counsel — Double-click to launch
REM  Creates a desktop shortcut on first run.
REM ============================================================
setlocal
cd /d "%~dp0"

REM --- Activate venv if present ---
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PY=%~dp0.venv\Scripts\python.exe"
) else (
    set "PY=py"
)

REM --- Start Streamlit (background) ---
start "Elite Business Counsel" /min cmd /c ""%PY%" -m streamlit run "%~dp0main.py" --server.headless true --server.port 8501"

REM --- Wait for server to start ---
echo Starting Elite Business Counsel...
timeout /t 4 /nobreak >nul

REM --- Open browser ---
start http://localhost:8501

echo.
echo  Elite Business Counsel is running at http://localhost:8501
echo  Close this window to stop the server.
echo.
pause
taskkill /fi "WINDOWTITLE eq Elite Business Counsel" >nul 2>&1
