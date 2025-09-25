#!/usr/bin/env sh
set -e

# Start Streamlit (served under /team1f25)
exec streamlit run app.py \
  --server.port=5001 \
  --server.address=0.0.0.0 \
  --server.baseUrlPath=team1f25 \
  --server.enableCORS=false \
  --server.enableXsrfProtection=false
