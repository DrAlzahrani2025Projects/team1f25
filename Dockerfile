# Dockerfile
FROM python:3.11-slim

# Workdir
WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY app /app/app
COPY main.py /app/main.py

# Streamlit runtime env (we still explicitly pass in CMD flags)
ENV PYTHONUNBUFFERED=1

# Expose required port
EXPOSE 5001

# Start Streamlit on port 5001, base path /team1f25, CORS disabled
CMD ["streamlit", "run", "main.py", "--server.port=5001", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.baseUrlPath=/team1f25"]
