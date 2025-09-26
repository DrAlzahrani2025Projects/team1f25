#!/usr/bin/env bash
set -euo pipefail

# ---Docker Configuration---
DOCKER_APP_IMAGE="team1f25-app"
DOCKER_CONTAINER_NAME="team1f25-app-container"
DOCKER_APP_PORT="5001"
DOCKER_WORKDIR="./team1f25-app"

CLEANUP_SCRIPT="docker-cleanup.sh"

if [[ ! -d "${DOCKER_WORKDIR}" ]]; then
  echo "Error: Directory '${DOCKER_WORKDIR}' not found. Exiting."
  exit 1
fi

# -- Run cleanup before building --
if [[ -x "${CLEANUP_SCRIPT}" ]]; then
  "./${CLEANUP_SCRIPT}" "${DOCKER_APP_IMAGE}" "${DOCKER_CONTAINER_NAME}"
else
  echo "Warning: Cleanup script not found or not executable at '${CLEANUP_SCRIPT}'. Skipping cleanup."
fi

cd "${DOCKER_WORKDIR}"

echo "🔨 Building image ${DOCKER_APP_IMAGE}..."
docker build -t "${DOCKER_APP_IMAGE}" .

echo "🚀 Running container ${DOCKER_CONTAINER_NAME} on :${DOCKER_APP_PORT}..."
docker run -d --restart unless-stopped \
  --name "${DOCKER_CONTAINER_NAME}" \
  -p "${DOCKER_APP_PORT}:${DOCKER_APP_PORT}" \
  "${DOCKER_APP_IMAGE}:latest"

echo "✅ Docker setup complete."
cd - >/dev/null 2>&1
