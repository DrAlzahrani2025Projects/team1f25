FROM python:3.11-slim

# Set the working directory inside the container to app
WORKDIR /app 

# Install Streamlit (lightweight installation, no cached files to save space)
RUN pip install --no-cache-dir streamlit

# Copied the application file (app.py) from local machine into container’s /app folder
COPY app.py .

CMD ["streamlit", "run", "app.py", "--server.port=5001", "--server.address=0.0.0.0", "--server.baseUrlPath=team1f25", "--server.enableCORS=false"]
