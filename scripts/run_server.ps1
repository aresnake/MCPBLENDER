param(
    [string]$Python = "python"
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $repoRoot
$env:PYTHONPATH = "$repoRoot/server_mcp/src"
Set-Location $repoRoot
& $Python -m mcpblender_server.server
