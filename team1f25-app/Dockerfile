FROM python:3.11-slim

WORKDIR /app

# Install Streamlit only
RUN pip install --no-cache-dir streamlit

COPY app.py .
COPY start.sh .
RUN chmod +x start.sh

EXPOSE 5001

CMD ["sh", "start.sh"]
