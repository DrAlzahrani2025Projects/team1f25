# Dockerfile
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app/app
COPY main.py /app/main.py

RUN mkdir -p /data /data/primo
ENV PYTHONUNBUFFERED=1
EXPOSE 5001

CMD ["streamlit", "run", "main.py", "--server.port=5001", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.baseUrlPath=/team1f25"]
