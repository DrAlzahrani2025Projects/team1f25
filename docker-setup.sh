#!/usr/bin/env bash
set -euo pipefail

# Run from this script's directory
cd "$(dirname "$0")"

echo "🧹 Cleaning old container(s) and image ..."

# Remove the named container if it exists
docker rm -f team1f25-app-container >/dev/null 2>&1 || true

# Remove any containers created from the image (if any)
ids="$(docker ps -aq --filter ancestor=team1f25-app || true)"
if [ -n "${ids}" ]; then
  docker rm -f ${ids}
fi

# Remove the image if it exists
docker rmi -f team1f25-app >/dev/null 2>&1 || true

echo "🔨 Building image team1f25-app ..."
docker build -t team1f25-app team1f25-app

echo "🚀 Running container team1f25-app-container on :5001 ..."
docker run -d --name team1f25-app-container -p 5001:5001 team1f25-app:latest

echo "✅ Done."
