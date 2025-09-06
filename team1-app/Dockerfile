# Use lightweight Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir flask gunicorn

# Copy your app into the container
COPY app.py .

# Run gunicorn as the server
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:5001", "app:app"]
