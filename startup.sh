#!/usr/bin/env bash
set -Eeuo pipefail

# Run the cleanup script first
./cleanup.sh --hard > /dev/null 2>&1 || true

# Ask for the API key
echo "Please enter your Groq API key:"
read -s GROQ_API_KEY
echo

# Build the Docker image
echo "Building Docker image..."
DOCKER_BUILDKIT=1 docker build -t team1f25-streamlit .

# Run the Docker container
echo "Starting Docker container..."
docker run -d -p 5001:5001 -e GROQ_API_KEY="$GROQ_API_KEY" --name team1f25 team1f25-streamlit

echo "Application is running on http://localhost:5001/team1f25"
