#!/usr/bin/env bash
set -euo pipefail

# Navigate to the directory containing this script (so it works from anywhere)
cd "$(dirname "$0")"

# stop and remove any existing container named team1f25-app-container
if [ "$(docker ps -aq -f name=team1f25-app-container)" ]; then
    echo "Stopping and removing existing container..."
    docker stop team1f25-app-container
    docker rm team1f25-app-container
fi

# remove any existing image named team1f25-app
if [ "$(docker images -q team1f25-app)" ]; then
    echo "Removing existing image..."
    docker rmi team1f25-app
fi

# docker build image team1f25-app
echo "Building Docker image for the application..."
docker build -t team1f25-app -f team1f25-app/Dockerfile team1f25-app

# docker run container from image team1f25-app in port 5001
echo "Running Docker container for the application on port 5001..."
docker run -d -p 5001:5001 --name team1f25-app-container team1f25-app:latest