$ErrorActionPreference = 'Stop'
$name = 'apache-proxy-local'

Write-Host "Stopping and removing $name..."
docker rm -f $name 2>$null | Out-Null
Write-Host "Done."
