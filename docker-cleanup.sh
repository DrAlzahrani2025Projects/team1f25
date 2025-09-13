#!/usr/bin/env bash
set -euo pipefail

# Run from this script's directory
cd "$(dirname "$0")"

echo "🧹 Cleaning up team1f25-app ..."

# Remove the named container if it exists
docker rm -f team1f25-app-container >/dev/null 2>&1 || true

# Remove any containers created from the image
ids="$(docker ps -aq --filter ancestor=team1f25-app || true)"
if [ -n "${ids}" ]; then
  docker rm -f ${ids}
fi

# Remove the image if it exists
docker rmi -f team1f25-app >/dev/null 2>&1 || true

echo "✅ Done."
