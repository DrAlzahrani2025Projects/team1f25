#!/usr/bin/env bash
set -Eeuo pipefail

# Stop the Docker container if it exists
echo "Stopping Docker container..."
docker stop team1f25 2>/dev/null || echo "Container 'team1f25' not running or does not exist."

# Remove the Docker container if it exists
echo "Removing Docker container..."
docker rm team1f25 2>/dev/null || echo "Container 'team1f25' not found."

# Remove the Docker image
echo "Removing Docker image..."
docker rmi team1f25-streamlit 2>/dev/null || echo "Image 'team1f25-streamlit' not found."

echo "Cleanup complete."
