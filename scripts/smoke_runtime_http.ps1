$ErrorActionPreference = "Stop"

Write-Host "=== MCPBLENDER Blender Runtime HTTP Smoke ==="

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
Set-Location $repoRoot

$baseUrl = "http://127.0.0.1:9876"

function Invoke-SmokeGet {
    param([string]$Path)

    $url = "$baseUrl$Path"
    Write-Host "`nGET $url"
    $resp = Invoke-RestMethod -Method Get -Uri $url
    $resp | ConvertTo-Json -Depth 6
}

Invoke-SmokeGet "/health"
Invoke-SmokeGet "/runtime/probe"
Invoke-SmokeGet "/scene/objects"
