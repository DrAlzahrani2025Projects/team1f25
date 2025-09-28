#!/usr/bin/env bash
set -euo pipefail

a2enmod proxy
a2enmod proxy_http
a2enmod proxy_wstunnel
a2enmod rewrite
a2enmod headers

a2dissite 000-default || true
a2ensite team1f25

# Run Streamlit on 8501 at root (no baseUrlPath)
python3 -m streamlit run /app/app.py \
  --server.address 0.0.0.0 \
  --server.port 8501 \
  --server.headless true \
  --browser.gatherUsageStats false &

exec apache2ctl -D FOREGROUND
