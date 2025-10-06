#!/usr/bin/env bash
set -euo pipefail

# stopping team1f25 container
docker ps -q --filter "name=team1f25" | xargs -r docker stop

# removing team1f25 container
docker ps -a -q --filter "name=team1f25" | xargs -r docker rm

# stopping ollama container
docker ps -q --filter "name=ollama-con" | xargs -r docker stop

# removing ollama container
docker ps -a -q --filter "name=ollama-con" | xargs -r docker rm


# deleting the team1f25-streamlit:latest image
docker images --filter "reference=team1f25-streamlit:latest" -q | xargs -r docker rmi



