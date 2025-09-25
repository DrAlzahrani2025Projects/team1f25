#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -eq 1 ] && [ "$1" = "local" ]; then
  echo "--- Local deployment ---"
  chmod +x build-deploy-app.sh
  ./build-deploy-app.sh
  echo "✅ Local app available at: http://localhost:5001/team1f25/"
  echo "✅ Local Jupyter at:     http://localhost:8888/team1f25-jupyter/"
else
  echo "--- Remote deployment ---"
  chmod +x build-deploy-app.sh apache-setup.sh
  ./build-deploy-app.sh
  sudo ./apache-setup.sh
  echo "✅ Remote app available at: https://sec.cse.csusb.edu/team1f25/"
  echo "✅ Remote Jupyter at:       https://sec.cse.csusb.edu/team1f25-jupyter/"
fi
