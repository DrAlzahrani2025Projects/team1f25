FROM python:3.11-slim

# Set the working directory inside the container to app
WORKDIR /app 

# Install Streamlit (lightweight installation, no cached files to save space)
RUN pip install --no-cache-dir streamlit jupyter

# Copied the application file (app.py) from local machine into container’s /app folder
COPY app.py .

# Add startup script to run Streamlit and Jupyter together
COPY start.sh .
RUN chmod +x start.sh

# Expose Streamlit (5001) and Jupyter (8888)
EXPOSE 5001 8888

# Start both services
CMD ["sh", "start.sh"]
