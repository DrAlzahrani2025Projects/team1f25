#!/usr/bin/env bash
set -euo pipefail

# Navigate to the directory containing this script (so it works from anywhere)
cd "$(dirname "$0")"

echo "Stopping and removing containers, networks, and volumes for this project..."
docker-compose down --remove-orphans

echo "✅ Cleanup complete."
