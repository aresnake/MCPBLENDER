param(
    [string]$Blender = "blender"
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $repoRoot
$addonPath = Join-Path $repoRoot "blender_addon"
$env:PYTHONPATH = "$addonPath"

Write-Host "Starting Blender bridge HTTP server (requires bpy)..."
& $Blender --background --python (Join-Path $addonPath "mcpblender_addon/bridge_http/server.py")
