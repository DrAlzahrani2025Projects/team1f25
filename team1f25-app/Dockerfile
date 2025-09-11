FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir streamlit

COPY app.py .

CMD ["streamlit", "run", "app.py", "--server.port=5001", "--server.address=0.0.0.0"]
