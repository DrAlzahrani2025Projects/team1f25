FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .

# create data dir for the SQLite DB
RUN mkdir -p /app/data
EXPOSE 5001

CMD ["streamlit","run","app.py","--server.port=5001","--server.address=0.0.0.0","--server.enableCORS=false"]
