# Push this folder to GitHub (run on your machine in PowerShell).
# Prereqs: Git installed; once: git config --global user.name "..." and user.email "..."
# Usage:
#   powershell -ExecutionPolicy Bypass -File "C:\Users\travi\Projects\AI Lawyer Build\PUSH_NOW.ps1"
# Or from project root:
#   powershell -ExecutionPolicy Bypass -File .\PUSH_NOW.ps1

$ErrorActionPreference = "Stop"
$Root = "C:\Users\travi\Projects\AI Lawyer Build"
$RemoteUrl = "https://github.com/Mr-Skyline/Sal---Skyline-Agentic-Lawyer.git"

function Find-GitExe {
    foreach ($p in @(
        "C:\Program Files\Git\cmd\git.exe",
        "C:\Program Files\Git\bin\git.exe",
        "${env:ProgramFiles(x86)}\Git\cmd\git.exe",
        "${env:ProgramFiles(x86)}\Git\bin\git.exe",
        "$env:LOCALAPPDATA\Programs\Git\cmd\git.exe"
    )) {
        if ($p -and (Test-Path -LiteralPath $p)) { return $p }
    }
    $cmd = Get-Command git -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

$git = Find-GitExe
if (-not $git) {
    Write-Host "Git not found. Install with:" -ForegroundColor Red
    Write-Host "  winget install Git.Git -e --source winget"
    Write-Host "Then close PowerShell, open a new window, and run this script again."
    exit 1
}

Write-Host "Using Git: $git" -ForegroundColor Cyan
Set-Location -LiteralPath $Root

$gemail = & $git config user.email 2>$null
$gname = & $git config user.name 2>$null
if (-not $gemail -or -not $gname) {
    Write-Host ""
    Write-Host "Git needs your name and email once (for commit history). Run:" -ForegroundColor Yellow
    Write-Host "  & `"$git`" config --global user.name `"Your Name`""
    Write-Host "  & `"$git`" config --global user.email `"you@example.com`""
    Write-Host "Then run this script again."
    exit 1
}

if (-not (Test-Path -LiteralPath "$Root\.git")) {
    & $git init -b main
}

& $git add -A
& $git status

$status = & $git status --porcelain
if ($status) {
    & $git commit -m "Initial commit: Sal Skyline Lawyer internal build"
} else {
    Write-Host "Nothing new to commit (working tree clean)." -ForegroundColor Yellow
}

$origin = & $git config --get remote.origin.url
if (-not $origin) {
    & $git remote add origin $RemoteUrl
    Write-Host "Added remote origin." -ForegroundColor Green
} elseif ($origin -ne $RemoteUrl) {
    & $git remote set-url origin $RemoteUrl
    Write-Host "Updated remote origin URL." -ForegroundColor Green
}

& $git branch -M main

Write-Host ""
Write-Host "Pushing to GitHub (browser or credential prompt may open)..." -ForegroundColor Cyan
& $git push -u origin main

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "If the remote already has commits (README, etc.), run then re-push:" -ForegroundColor Yellow
    Write-Host "  Set-Location `"$Root`""
    Write-Host "  & `"$git`" pull origin main --rebase --allow-unrelated-histories"
    Write-Host "  & `"$git`" push -u origin main"
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Done. Repo: https://github.com/Mr-Skyline/Sal---Skyline-Agentic-Lawyer" -ForegroundColor Green
