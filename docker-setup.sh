#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME=team1f25:latest
CONTAINER_NAME=team1f25

docker build -t "$IMAGE_NAME" .

if [ "$(docker ps -aq -f name="^${CONTAINER_NAME}$")" ]; then
  docker rm -f "$CONTAINER_NAME" || true
fi

docker run -d --name "$CONTAINER_NAME" -p 5001:5001 "$IMAGE_NAME"

echo "Container started. Visit: http://localhost:5001/team1f25"
