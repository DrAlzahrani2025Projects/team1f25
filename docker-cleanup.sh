#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME=team1f25
IMAGE_NAME=team1f25:latest

docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
docker rmi -f "$IMAGE_NAME" 2>/dev/null || true

echo "Cleaned up container and image."
