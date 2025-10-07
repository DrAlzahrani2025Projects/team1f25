
FROM python:3.11-slim
# Avoid Python buffering and pip cache
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Copy dependency list first (better layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install -r requirements.txt

# Copy app source code
COPY app.py . 

EXPOSE 5001

CMD ["streamlit", "run", "app.py", "--server.port=5001", "--server.address=0.0.0.0", "--server.enableCORS=false","--server.baseUrlPath=/team1f25"]
