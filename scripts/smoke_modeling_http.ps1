$ErrorActionPreference = "Stop"

Write-Host "=== MCPBLENDER Modeling HTTP Smoke ==="

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
Set-Location $repoRoot

$baseUrl = "http://127.0.0.1:9876"

function Invoke-PostJson {
    param([string]$Path, [hashtable]$Body = @{})

    $url = "$baseUrl$Path"
    Write-Host "`nPOST $url"
    $json = ($Body | ConvertTo-Json -Depth 6)
    $resp = Invoke-RestMethod -Method Post -Uri $url -Body $json -ContentType "application/json"
    $resp | ConvertTo-Json -Depth 6
}

function Invoke-GetJson {
    param([string]$Path)
    $url = "$baseUrl$Path"
    Write-Host "`nGET $url"
    $resp = Invoke-RestMethod -Method Get -Uri $url
    $resp | ConvertTo-Json -Depth 6
}

Invoke-PostJson "/scene/reset" @{}
Invoke-PostJson "/mesh/add_cube" @{ name = "Cube"; size = 2.0; location = @(0, 0, 0) }
Invoke-PostJson "/mesh/add_plane" @{ name = "Ground"; size = 4.0; location = @(0, 0, -1) }
Invoke-PostJson "/mesh/add_cylinder" @{ name = "Cyl"; radius = 0.5; depth = 2.0; vertices = 24; location = @(2, 0, 0) }
Invoke-PostJson "/object/transform" @{ name = "Cube"; location = @(1, 2, 3); rotation_euler = @(0.1, 0.2, 0.3); scale = @(1.5, 1.5, 1.5); delta = $false }
Invoke-GetJson "/scene/objects"
