#!/usr/bin/env bash
set -euo pipefail

# Navigate to the directory containing this script (so it works from anywhere)
cd "$(dirname "$0")"

echo "🛑 Stopping any existing containers..."
docker-compose down --remove-orphans

echo "🔨 Building fresh images..."
docker-compose build --no-cache

echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "✅ Setup complete. Services are running."
echo ""
echo "You can now access your apps at:"
echo "  • Team1 App:       http://localhost:2501/team1/"
echo "  • Team1 Jupyter:   http://localhost:2501/team1/jupyter/"
echo ""
