#!/usr/bin/env bash
set -euo pipefail

chmod +x build-deploy-app.sh apache-setup.sh docker-cleanup.sh
./build-deploy-app.sh
./apache-setup.sh
echo "✅ Remote app available at: https://sec.cse.csusb.edu/team1f25/"
