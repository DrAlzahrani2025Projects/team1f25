#!/usr/bin/env bash
set -euo pipefail

# Navigate to the directory containing this script (so it works from anywhere)
cd "$(dirname "$0")"

# stop and remove any container named team1f25-app-container and its dependencies
if [ "$(docker ps -q -f name=team1f25-app-container)" ]; then
    echo "Stopping container team1f25-app-container..."
    docker stop team1f25-app-container
    docker rm team1f25-app-container
fi

# remove any image named team1f25-app
if [ "$(docker images -q team1f25-app)" ]; then
    echo "Removing image team1f25-app..."
    docker rmi team1f25-app
fi
