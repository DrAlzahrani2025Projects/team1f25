#!/usr/bin/env bash
set -Eeuo pipefail

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Run the cleanup script first
"$SCRIPT_DIR/cleanup.sh" --hard > /dev/null 2>&1 || true

# Ask for the API key
echo "Please enter your Groq API key:"
read -s GROQ_API_KEY
echo

# Change to project root
cd "$PROJECT_ROOT"

# Export API key for docker-compose
export GROQ_API_KEY

# Start services with docker-compose (Nginx + Streamlit with CSP headers)
echo "Starting application with CSP security headers..."
docker-compose up -d

echo "✅ Application is running on http://localhost:5001/team1f25"
echo "🔒 CSP Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; connect-src 'self' ws: wss:; frame-ancestors 'none';"
