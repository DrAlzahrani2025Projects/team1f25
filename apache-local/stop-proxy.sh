#!/usr/bin/env bash
set -euo pipefail

NAME="apache-proxy-local"
echo "Stopping and removing $NAME..."
docker rm -f "$NAME" >/dev/null 2>&1 || true
echo "Done."
