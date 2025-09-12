#!/usr/bin/env bash
set -euo pipefail

# Navigate to the directory containing this script (so it works from anywhere)
cd "$(dirname "$0")"

echo "🛑 Stopping any existing containers..."
docker compose down --remove-orphans

echo "🔨 Building fresh images..."
docker compose build --no-cache

echo "🚀 Starting services..."
docker compose up -d

echo ""
echo "✅ Setup complete. Services are running."
echo ""
echo "You can now access your apps at:"
echo "  • Team1f25 App:       http://sec.cse.csusb.edu/team1f25"
echo "  • Team1f25 Jupyter:   http://sec.cse.csusb.edu/team1f25/jupyter"
echo ""
