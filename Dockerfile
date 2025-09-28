FROM python:3.11-slim

WORKDIR /app
COPY app.py /app/app.py

RUN pip install --no-cache-dir streamlit==1.37.1

EXPOSE 5001

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=5001", "--server.baseUrlPath=team1f25"]
