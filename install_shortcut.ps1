<#
.SYNOPSIS
  Creates a desktop shortcut for Elite Business Counsel.
  Run once: powershell -ExecutionPolicy Bypass -File "install_shortcut.ps1"
#>
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$batPath     = Join-Path $projectRoot 'Launch Elite Business Counsel.bat'
$iconPath    = Join-Path $projectRoot 'assets\icon.ico'
$desktop     = [Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktop 'Elite Business Counsel.lnk'

if (-not (Test-Path $batPath)) {
    Write-Error "Missing: $batPath"
    exit 1
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $batPath
$shortcut.WorkingDirectory = $projectRoot
$shortcut.Description = 'Skyline Painting — Elite Business Counsel (Sal)'
$shortcut.WindowStyle = 1
if (Test-Path $iconPath) {
    $shortcut.IconLocation = "$iconPath,0"
}
$shortcut.Save()

Write-Host ""
Write-Host "  Shortcut created: $shortcutPath" -ForegroundColor Green
Write-Host "  Double-click it to launch the app." -ForegroundColor Cyan
Write-Host ""
