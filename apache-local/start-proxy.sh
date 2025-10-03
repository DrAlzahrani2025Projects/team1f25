#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-8080}"
IMG="httpd:2.4"
NAME="apache-proxy-local"

echo "Pulling $IMG..."
docker pull "$IMG"

echo "Removing existing container if any..."
docker rm -f "$NAME" >/dev/null 2>&1 || true

ROOT="$(pwd)"
# Resolve to absolute native paths; realpath is preferable if available
if command -v realpath >/dev/null 2>&1; then
  HTTPD_CONF="$(realpath "$ROOT/apache-local/httpd.conf")"
  VHOST_CONF="$(realpath "$ROOT/apache-local/team1f25-vhost.conf")"
else
  HTTPD_CONF="$ROOT/apache-local/httpd.conf"
  VHOST_CONF="$ROOT/apache-local/team1f25-vhost.conf"
fi

if [[ ! -f "$HTTPD_CONF" || ! -f "$VHOST_CONF" ]]; then
  echo "Config files not found. Expected $HTTPD_CONF and $VHOST_CONF" >&2
  exit 1
fi

echo "Starting $NAME on port $PORT..."
cid=$(docker run -d \
  --name "$NAME" \
  --mount type=bind,source="$HTTPD_CONF",target=/usr/local/apache2/conf/httpd.conf,readonly \
  --mount type=bind,source="$VHOST_CONF",target=/usr/local/apache2/conf/extra/team1f25-vhost.conf,readonly \
  -p "$PORT:80" \
  "$IMG")

sleep 2
docker logs --tail 50 "$NAME"
echo "Container ID: $cid"
echo "Proxy running: http://localhost:$PORT/team1f25/"
echo "Hint: If using Git Bash on Windows, export MSYS_NO_PATHCONV=1 before running to avoid path mangling."

# Quick health checks
for path in team1f25 team1f25-jupyter; do
  code=$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:$PORT/$path/") || code="ERR"
  echo "Health: /$path/ -> $code"
done
