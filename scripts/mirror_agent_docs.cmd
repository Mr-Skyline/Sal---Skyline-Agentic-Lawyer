@echo off
REM Sync agent-facing docs + Cursor rules with a second checkout (optional).
REM Set SKYLINE_MIRROR_STACK to the other tree's path, or pass it as the second argument:
REM   mirror_agent_docs.cmd default "D:\path\to\other\checkout"
REM NOT copied (reconcile manually across two working trees if needed):
REM   SKYLINE_BUILD_REVIEW.md, OPERATIONS_ELITE.txt, TRACK_D_*.md, application .py files.
setlocal
cd /d "%~dp0.."
set "HERE=%CD%"
set "STACK=%SKYLINE_MIRROR_STACK%"
if not "%~2"=="" set "STACK=%~2"
if "%STACK%"=="" (
  echo ERROR: Set SKYLINE_MIRROR_STACK to the canonical stack folder, or pass it as the second argument.
  exit /b 1
)

if /i "%~1"=="backup" goto FROM_STACK
if /i "%~1"=="fromstack" goto FROM_STACK

goto TO_STACK

:TO_STACK
if not exist "%STACK%\" (
  echo ERROR: Stack folder not found: %STACK%
  exit /b 1
)
echo Pushing agent docs TO stack: %STACK%
if not exist "%STACK%\scripts\" mkdir "%STACK%\scripts\"
copy /Y "%HERE%\scripts\mirror_agent_docs.cmd" "%STACK%\scripts\"
copy /Y "%HERE%\AGENTS.md" "%STACK%\"
copy /Y "%HERE%\AGENT_TEAM_CHECKLIST.md" "%STACK%\"
if not exist "%STACK%\.cursor\rules\" mkdir "%STACK%\.cursor\rules"
copy /Y "%HERE%\.cursor\rules\agent-team-checklist.mdc" "%STACK%\.cursor\rules\"
copy /Y "%HERE%\.cursor\rules\agent-autonomy.mdc" "%STACK%\.cursor\rules\"
echo Done.
exit /b 0

:FROM_STACK
if not exist "%STACK%\AGENTS.md" (
  echo ERROR: Nothing to pull — missing %STACK%\AGENTS.md
  exit /b 1
)
echo Pulling agent docs FROM stack into: %HERE%
if not exist "%HERE%\scripts\" mkdir "%HERE%\scripts\"
if exist "%STACK%\scripts\mirror_agent_docs.cmd" copy /Y "%STACK%\scripts\mirror_agent_docs.cmd" "%HERE%\scripts\"
copy /Y "%STACK%\AGENTS.md" "%HERE%\"
copy /Y "%STACK%\AGENT_TEAM_CHECKLIST.md" "%HERE%\"
if not exist "%HERE%\.cursor\rules\" mkdir "%HERE%\.cursor\rules"
copy /Y "%STACK%\.cursor\rules\agent-team-checklist.mdc" "%HERE%\.cursor\rules\"
copy /Y "%STACK%\.cursor\rules\agent-autonomy.mdc" "%HERE%\.cursor\rules\"
echo Done.
exit /b 0
