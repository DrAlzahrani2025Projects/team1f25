#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -eq 1 ] && [ "$1" = "local" ]; then
  echo "--- Local deployment ---"
  ./docker-setup.sh
  echo "✅ Local app available at: http://localhost:5001/team1f25/"
else
  echo "--- Remote deployment ---"
  ./docker-setup.sh
  sudo ./apache-setup.sh
  echo "✅ Remote app available at: https://sec.cse.csusb.edu/team1f25/"
fi
