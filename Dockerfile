
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./
# Default environment (override at runtime)
ENV OLLAMA_URL=http://host.docker.internal:11434
ENV LLM_MODEL=tinyllama:latest

EXPOSE 5001

CMD ["streamlit", "run", "app.py", "--server.port=5001", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.baseUrlPath=/team1f25"]
