#!/usr/bin/env bash
set -Eeuo pipefail

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Run the cleanup script first
"$SCRIPT_DIR/cleanup.sh" > /dev/null 2>&1 || true

# Ask for the API key
echo "Please enter your Groq API key:"
read -s GROQ_API_KEY
echo

# Change to project root for Docker commands
cd "$PROJECT_ROOT"

# Build the Docker image
echo "Building Docker image..."
DOCKER_BUILDKIT=1 docker build -f docker/Dockerfile -t team1f25-streamlit .

# Run the Docker container
echo "Starting Docker container..."
docker run -d -p 5001:5001 -e GROQ_API_KEY="$GROQ_API_KEY" --name team1f25 team1f25-streamlit

echo "Application is running on http://localhost:5001/team1f25"
