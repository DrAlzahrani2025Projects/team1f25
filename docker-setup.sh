#!/usr/bin/env bash
set -euo pipefail

sudo chmod +x build-deploy-app.sh apache-setup.sh docker-cleanup.sh
sudo ./build-deploy-app.sh
sudo ./apache-setup.sh
echo "✅ Remote app available at: https://sec.cse.csusb.edu/team1f25/"
