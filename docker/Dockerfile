FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/data

WORKDIR /app
COPY requirements.txt .
# Upgrade pip to specific version for security
RUN python -m pip install --upgrade pip==25.3 && \
    pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY core/ core/
COPY ui/ ui/

RUN useradd -m appuser && mkdir -p /data && chown -R appuser:appuser /data /app
USER appuser

EXPOSE 5001
CMD ["streamlit", "run", "app.py", "--server.port=5001", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.baseUrlPath=/team1f25"]
