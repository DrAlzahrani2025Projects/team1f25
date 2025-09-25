#!/usr/bin/env sh
set -e

# Start Streamlit (served under /team1f25)
streamlit run app.py \
  --server.port=5001 \
  --server.address=0.0.0.0 \
  --server.baseUrlPath=team1f25 \
  --server.enableCORS=false \
  --server.enableXsrfProtection=false &

# Start Jupyter Notebook (served under /team1f25-jupyter)
exec jupyter notebook \
  --ip=0.0.0.0 \
  --port=8888 \
  --no-browser \
  --NotebookApp.token='' \
  --NotebookApp.base_url=/team1f25-jupyter \
  --allow-root
