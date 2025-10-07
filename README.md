# team1f25 — TinyLlama Chat (fast CPU)

## Run with ONLY Python (quickest test)
pip install -r requirements.txt
streamlit run app.py
# Open: http://localhost:8501

## Build & Run with DOCKER
# Build
docker build --no-cache -f docker -t team1f25-streamlit:latest .

# Run (model cached to a volume; no baseUrlPath → simple URL)
docker run -d -p 5001:5001 --name team1f25 \
  -v tinycache:/models \
  team1f25-streamlit:latest

# Open
http://localhost:5001

## If the model file is gated for your account
# 1) Create a .env file next to app.py:
#    HUGGINGFACE_HUB_TOKEN=hf_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# 2) Pass it at runtime:
docker rm -f team1f25
docker run -d -p 5001:5001 --name team1f25 \
  --env-file .env \
  -v tinycache:/models \
  team1f25-streamlit:latest
