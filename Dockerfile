
FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install streamlit

EXPOSE 5001

CMD ["streamlit", "run", "app.py", "--server.port=5001", "--server.address=0.0.0.0", "--server.enableCORS=false"]
