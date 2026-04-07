@echo off
REM Sync agent-facing docs + Cursor rules with the canonical stack (INTENDED_PROJECT_ROOT).
REM Edit STACK below if config.py INTENDED_PROJECT_ROOT ever changes.
REM NOT copied here (reconcile manually across two working trees if needed):
REM   docs/SKYLINE_BUILD_REVIEW.md, docs/OPERATIONS_ELITE.txt, TRACK_D_*.md, application .py files.
setlocal
set "STACK=C:\Users\travi\Projects\AI Lawyer Build"
set "HERE=%~dp0"
set "HERE=%HERE:~0,-1%"

if /i "%~1"=="backup" goto FROM_STACK
if /i "%~1"=="fromstack" goto FROM_STACK

REM Default: push from this folder → STACK (only when HERE and STACK are two different trees).
goto TO_STACK

:TO_STACK
if not exist "%STACK%\" (
  echo ERROR: Stack folder not found: %STACK%
  exit /b 1
)
echo Pushing agent docs TO stack: %STACK%
copy /Y "%HERE%\mirror_agent_docs.cmd" "%STACK%\"
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
echo Pulling agent docs FROM stack into backup copy: %HERE%
if exist "%STACK%\mirror_agent_docs.cmd" copy /Y "%STACK%\mirror_agent_docs.cmd" "%HERE%\"
copy /Y "%STACK%\AGENTS.md" "%HERE%\"
copy /Y "%STACK%\AGENT_TEAM_CHECKLIST.md" "%HERE%\"
if not exist "%HERE%\.cursor\rules\" mkdir "%HERE%\.cursor\rules"
copy /Y "%STACK%\.cursor\rules\agent-team-checklist.mdc" "%HERE%\.cursor\rules\"
copy /Y "%STACK%\.cursor\rules\agent-autonomy.mdc" "%HERE%\.cursor\rules\"
echo Done.
exit /b 0
