$ErrorActionPreference = "Stop"

Write-Host "=== MCPBLENDER Blender Runtime HTTP ==="

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
Set-Location $repoRoot

$candidates = @()
if ($env:BLENDER_EXE) { $candidates += $env:BLENDER_EXE }
$candidates += "C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
$candidates += "D:\Blender_5.0.0_Portable\blender.exe"

$blenderExe = $candidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $blenderExe) {
    Write-Error "Blender executable not found. Set BLENDER_EXE or install Blender 5.0."
    exit 1
}

Write-Host "Using Blender at $blenderExe"
& $blenderExe --background --python "runtime_blender/http_runtime_server.py" -- --port 9876

exit $LASTEXITCODE
