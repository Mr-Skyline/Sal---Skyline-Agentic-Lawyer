# One-time: local Git repo + first commit, then push to your GitHub remote.
# Requires: Git for Windows (https://git-scm.com/download/win) or: winget install Git.Git -e --source winget
# Run from project root:  powershell -ExecutionPolicy Bypass -File .\init_for_github.ps1
# First push (finds Git if not on PATH): use PUSH_NOW.ps1 instead.

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# Canonical remote for this build (inspectors / collaborators)
$RemoteUrl = "https://github.com/Mr-Skyline/Sal---Skyline-Agentic-Lawyer.git"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "Git not found on PATH."
    Write-Host "Install Git, restart this terminal, then run this script again."
    Write-Host "Example: winget install Git.Git -e --source winget"
    exit 1
}

if (Test-Path .git) {
    Write-Host "Already a Git repository." -ForegroundColor Cyan
    git status -sb
    git remote -v
    $originUrl = git config --get remote.origin.url
    if (-not $originUrl) {
        Write-Host ""
        Write-Host "No origin remote yet. Add and push:" -ForegroundColor Yellow
        Write-Host "  git remote add origin $RemoteUrl"
        Write-Host "  git push -u origin main"
        Write-Host ""
        Write-Host "If GitHub already has commits (e.g. README), use first:"
        Write-Host "  git pull origin main --rebase"
        Write-Host "  git push -u origin main"
    }
    exit 0
}

git init -b main
git add -A
git status
git commit -m "Initial commit: Sal Skyline Lawyer internal build"

Write-Host ""
Write-Host "=== Local repo ready. Push to GitHub ===" -ForegroundColor Cyan
Write-Host "  git remote add origin $RemoteUrl"
Write-Host "  git push -u origin main"
Write-Host ""
Write-Host "If the remote is not empty (you added a README on github.com), run first:"
Write-Host "  git pull origin main --rebase --allow-unrelated-histories"
Write-Host "  git push -u origin main"
Write-Host ""
Write-Host "Browser: https://github.com/Mr-Skyline/Sal---Skyline-Agentic-Lawyer"
Write-Host ".env, credentials.json, token.pickle, .venv, skyline_review/ stay out via .gitignore."
