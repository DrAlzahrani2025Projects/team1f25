# syntax=docker/dockerfile:1.6
FROM python:3.11-slim

WORKDIR /app

# 1) Install deps with pip cache (BuildKit)
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# 2) Copy source
COPY app /app/app
COPY main.py /app/main.py

# 3) (Optional) Pre-download the FastEmbed model to avoid first-run delay
RUN python - <<'PY'
from fastembed import TextEmbedding
TextEmbedding(model_name="BAAI/bge-small-en-v1.5")  # downloads to ~/.cache/fastembed
print("FastEmbed model cached.")
PY

# 4) Usual runtime
RUN mkdir -p /data /data/primo
ENV PYTHONUNBUFFERED=1
EXPOSE 5001

CMD ["streamlit", "run", "main.py", "--server.port=5001", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.baseUrlPath=/team1f25"]
