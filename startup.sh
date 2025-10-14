#!/usr/bin/env bash
set -Eeuo pipefail

# Run the cleanup script first
./cleanup.sh > /dev/null 2>&1 || true

HOST_DATA="$PWD/data"
if [[ -n "${MSYSTEM:-}" ]]; then
  # Git Bash/MSYS: use Windows-style path for the left side of -v
  if command -v pwd >/dev/null 2>&1 && pwd -W >/dev/null 2>&1; then
    HOST_DATA="$(pwd -W)/data"
  fi
fi
mkdir -p ./data

# Ask for the API key
echo "Please enter your Groq API key:"
read -s GROQ_API_KEY
echo
# Build the Docker image
echo "Building Docker image..."
DOCKER_BUILDKIT=1 docker build -t team1f25-streamlit .

MSYS_PREFIX=()
if [[ -n "${MSYSTEM:-}" ]]; then
  MSYS_PREFIX=(MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL="*")
fi

# Run the Docker container
echo "Starting Docker container..."
if [[ -n "${MSYSTEM:-}" ]]; then
  MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL="*" docker run -d -p 5001:5001 -e GROQ_API_KEY="$GROQ_API_KEY" -v "$HOST_DATA:/data" --name team1f25 team1f25-streamlit
else
  docker run -d -p 5001:5001 -e GROQ_API_KEY="$GROQ_API_KEY" -v "$HOST_DATA:/data" --name team1f25 team1f25-streamlit
fi

echo "Application is running on http://localhost:5001/team1f25"
