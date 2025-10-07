FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 5001

# default served at root; override via --env-file .env
ENV BASE_URL_PATH=""

# shell-form CMD so $BASE_URL_PATH is substituted at runtime
CMD streamlit run app.py \
    --server.headless=true \
    --server.port=5001 \
    --server.address=0.0.0.0 \
    --server.enableCORS=false \
    --server.baseUrlPath="$BASE_URL_PATH"
