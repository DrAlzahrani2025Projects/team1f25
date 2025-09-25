#!/usr/bin/env bash
set -euo pipefail

# --- Docker Configuration ---
DOCKER_APP_IMAGE="team1f25-app"
DOCKER_CONTAINER_NAME="team1f25-app-container"
DOCKER_APP_PORT="5001"
DOCKER_WORKDIR="./team1f25-app"

echo "--- Starting Docker application management ---"

if [ ! -d "$DOCKER_WORKDIR" ]; then
  echo "Error: Directory '$DOCKER_WORKDIR' not found. Exiting."
  exit 1
fi

cd "$DOCKER_WORKDIR"

echo "🧹 Cleaning old container(s) and image..."
docker rm -f "$DOCKER_CONTAINER_NAME" >/dev/null 2>&1 || true
ids="$(docker ps -aq --filter ancestor="$DOCKER_APP_IMAGE" || true)"
if [ -n "${ids}" ]; then
  docker rm -f ${ids} >/dev/null 2>&1 || true
fi
docker rmi -f "$DOCKER_APP_IMAGE" >/dev/null 2>&1 || true

echo "🔨 Building image $DOCKER_APP_IMAGE..."
docker build -t "$DOCKER_APP_IMAGE" .

echo "🚀 Running container $DOCKER_CONTAINER_NAME on :$DOCKER_APP_PORT and 8888..."
docker run -d --restart unless-stopped \
  --name "$DOCKER_CONTAINER_NAME" \
  -p "$DOCKER_APP_PORT":"$DOCKER_APP_PORT" \
  -p 8888:8888 \
  "$DOCKER_APP_IMAGE":latest

echo "✅ Docker setup complete."
cd - >/dev/null 2>&1
