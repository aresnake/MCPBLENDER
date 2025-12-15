param(
  [string]$BindHost = "127.0.0.1",
  [int]$Port = 9876
)

Write-Host "=== MCPBLENDER Blender Runtime HTTP ===" -ForegroundColor Cyan

$blenderExe = $env:BLENDER_EXE
if (-not $blenderExe -or -not (Test-Path $blenderExe)) {
  $fallback1 = "C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
  $fallback2 = "D:\Blender_5.0.0_Portable\blender.exe"
  if (Test-Path $fallback1) { $blenderExe = $fallback1 }
  elseif (Test-Path $fallback2) { $blenderExe = $fallback2 }
  else { throw "BLENDER_EXE not set and no fallback Blender found." }
}

Write-Host ("Using Blender at " + $blenderExe) -ForegroundColor Yellow

$scriptPath = (Resolve-Path (Join-Path $PSScriptRoot "..\runtime_blender\http_runtime_server.py")).Path

# Important: pass args as an array so quoting/order are preserved
$blenderArgs = @(
  "--background",
  "--python", $scriptPath,
  "--",
  "--host", $BindHost,
  "--port", "$Port"
)

& $blenderExe @blenderArgs
