#!/usr/bin/env bash
set -euo pipefail

# Usage: docker-cleanup.sh <image> <container>
IMAGE="${1:-team1f25-app}"
CONTAINER="${2:-team1f25-app-container}"

echo "🧹 Cleaning old container(s) and image..."

# Stop & remove the named container (if provided/existing)
if [[ -n "${CONTAINER}" ]]; then
  docker rm -f "${CONTAINER}" >/dev/null 2>&1 || true
fi

# Remove any containers created from the image (if provided)
if [[ -n "${IMAGE}" ]]; then
  ids="$(docker ps -aq --filter "ancestor=${IMAGE}" || true)"
  if [[ -n "${ids}" ]]; then
    # shellcheck disable=SC2086
    docker rm -f ${ids} >/dev/null 2>&1 || true
  fi

  # Remove the image 
  docker rmi -f "${IMAGE}" >/dev/null 2>&1 || true
fi

echo "✅ Cleanup complete."
