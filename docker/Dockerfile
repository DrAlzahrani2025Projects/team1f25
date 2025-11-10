# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set environment variables:
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/data

# Set working directory inside the container
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .

# Upgrade pip to a specific version for security, then install dependencies
RUN python -m pip install --upgrade pip==25.3 && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code into the container
COPY app.py .
COPY core/ core/
COPY ui/ ui/


RUN useradd -m appuser && mkdir -p /data && chown -R appuser:appuser /data /app

USER appuser

# Expose Streamlit port
EXPOSE 5001

# Start the Streamlit app 
CMD ["streamlit", "run", "app.py", "--server.port=5001", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.baseUrlPath=/team1f25"]
