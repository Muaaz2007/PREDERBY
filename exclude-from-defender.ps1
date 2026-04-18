# Run this script as Administrator to exclude build folders from Windows Defender scans
# This prevents antivirus from locking executable files during and after PyInstaller builds

# Requires Administrator privileges
if (-Not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] 'Administrator')) {
    Write-Host "This script requires Administrator privileges. Please run PowerShell as Administrator." -ForegroundColor Red
    exit 1
}

$projectPath = Get-Location
$distPath = Join-Path $projectPath "dist"
$buildPath = Join-Path $projectPath "build"

Write-Host "Adding Windows Defender exclusions for build folders..." -ForegroundColor Green
Write-Host "Project path: $projectPath"

try {
    # Add dist folder to exclusions
    if (Test-Path $distPath) {
        Add-MpPreference -ExclusionPath $distPath -ErrorAction Stop
        Write-Host "[OK] Added exclusion: $distPath" -ForegroundColor Green
    }
    
    # Add build folder to exclusions
    if (Test-Path $buildPath) {
        Add-MpPreference -ExclusionPath $buildPath -ErrorAction Stop
        Write-Host "[OK] Added exclusion: $buildPath" -ForegroundColor Green
    }
    
    # Add the entire project folder as well (optional but recommended)
    Add-MpPreference -ExclusionPath $projectPath -ErrorAction Stop
    Write-Host "[OK] Added exclusion: $projectPath" -ForegroundColor Green
    
    Write-Host "`nWindows Defender exclusions added successfully!" -ForegroundColor Green
    Write-Host "Your builds should no longer encounter permission lock errors." -ForegroundColor Green
}
catch {
    Write-Host "Error adding exclusions: $_" -ForegroundColor Red
    exit 1
}
