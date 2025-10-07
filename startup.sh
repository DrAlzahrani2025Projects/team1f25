#!/bin/bash

# Run the cleanup script first
./cleanup.sh > /dev/null 2>&1

# Ask for the API key
echo "Please enter your Groq API key:"
read -s GROQ_API_KEY
echo
# Build the Docker image
echo "Building Docker image..."
docker build -t team1f25-streamlit .

# Run the Docker container
echo "Starting Docker container..."
docker run -d -p 5001:5001 -e GROQ_API_KEY="$GROQ_API_KEY" -v "$(pwd)/data":/app/data --name team1f25 team1f25-streamlit

echo "Application is running on http://localhost:5001"
