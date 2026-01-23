param(
    [string]$TargetDir = "$env:USERPROFILE\.local\bin"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Source = Join-Path $ScriptDir "..\pp.py"

if (-Not (Test-Path $Source)) {
    Write-Error "pp.py not found relative to $ScriptDir"
    exit 1
}

New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
$Target = Join-Path $TargetDir "pp"

Copy-Item -Force -Path $Source -Destination $Target
icacls $Target /grant:r "*S-1-1-0:(RX)" > $null 2>&1
Write-Host "Installed pp to $Target"
