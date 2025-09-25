param(
  [int]$Port = 8080
)

$ErrorActionPreference = 'Stop'
$img = 'httpd:2.4'
$name = 'apache-proxy-local'

Write-Host "Pulling $img..."
docker pull $img | Out-Host

Write-Host "Removing existing container if any..."
try { docker rm -f $name 2>$null | Out-Null } catch { }

$root = (Get-Location).Path
$httpdConf = (Resolve-Path (Join-Path $root 'apache-local/httpd.conf')).ProviderPath
$vhostConf = (Resolve-Path (Join-Path $root 'apache-local/team1f25-vhost.conf')).ProviderPath

if (!(Test-Path $httpdConf) -or !(Test-Path $vhostConf)) {
  throw "Config files not found. Expected $httpdConf and $vhostConf"
}

Write-Host "Starting $name on port $Port..."
$runArgs = @(
  'run','-d',
  '--name', $name,
  '--mount', ("type=bind,source={0},target=/usr/local/apache2/conf/httpd.conf,readonly" -f $httpdConf),
  '--mount', ("type=bind,source={0},target=/usr/local/apache2/conf/extra/team1f25-vhost.conf,readonly" -f $vhostConf),
  '-p', ("{0}:80" -f $Port),
  $img
)
$cid = & docker @runArgs

Start-Sleep -Seconds 2
docker logs --tail 50 $name | Out-Host
Write-Host "Container ID: $cid"
Write-Host "Proxy running: http://localhost:$Port/team1f25/"
