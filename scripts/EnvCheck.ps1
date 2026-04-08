Set-Location (Join-Path $PSScriptRoot "..")
if (Test-Path ".\.venv\Scripts\python.exe") {
    & .\.venv\Scripts\python.exe scripts\env_check.py
} else {
    py scripts\env_check.py
}
exit $LASTEXITCODE
