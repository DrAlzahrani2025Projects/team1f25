# Use official Python runtime
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app.py .

# Expose port 5001
EXPOSE 5001

# Run Streamlit app on port 5001
CMD ["streamlit", "run", "app.py", "--server.port=5001", "--server.address=0.0.0.0"]

