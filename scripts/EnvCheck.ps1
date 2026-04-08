$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $RepoRoot
if (Test-Path ".\.venv\Scripts\python.exe") {
    & .\.venv\Scripts\python.exe .\env_check.py
} else {
    py .\env_check.py
}
exit $LASTEXITCODE
