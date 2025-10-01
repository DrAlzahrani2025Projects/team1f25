#!/usr/bin/env bash
set -euo pipefail

chmod +x build-deploy-app.sh docker-cleanup.sh
./build-deploy-app.sh
#sudo ./apache-setup.sh
