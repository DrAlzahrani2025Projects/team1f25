#!/usr/bin/env bash
set -euo pipefail

./docker-cleanup.sh

# run ollama container using the pulled image and assigning the port to 11434 also mounting the volumes from host path to container path
docker run -d --name ollama-con -p 11434:11434   -v ollama_models:/root/.ollama ollama/ollama:latest

# ollama is an actual framework/runtime for running/interacting with llms locally
# pull llm into ollama container
docker exec -it ollama-con ollama pull tinyllama

# list the llms
docker exec -it ollama-con ollama ls

# build team1f25-streamlit image
docker build -t team1f25-streamlit .

# run team1f25 container
docker run -d --name team1f25 -p 5001:5001  --add-host=host.docker.internal:host-gateway  -e OLLAMA_URL=http://host.docker.internal:11434   -e LLM_MODEL=tinyllama:latest   team1f25-streamlit



