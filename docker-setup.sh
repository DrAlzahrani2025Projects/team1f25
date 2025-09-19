#!/usr/bin/env bash

# Exit on error (-e), unset var (-u), fail in pipelines (-o pipefail)
set -euo pipefail

# --- Docker Configuration ---
DOCKER_APP_IMAGE="team1f25-app"
DOCKER_CONTAINER_NAME="team1f25-app-container"
DOCKER_APP_PORT="5001"
DOCKER_WORKDIR="./team1f25-app"  # Dockerfile is in this subdirectory

# --- Apache/Proxy Configuration ---
# Usage: ./deploy.sh [local]
# If "local" is passed, skip Apache config and just run Docker on localhost.
if [ "$#" -eq 1 ] && [ "$1" = "local" ]; then
  PROXY_DOMAIN="localhost"
  SKIP_APACHE=true
  echo "--- Local deployment requested. Skipping Apache configuration. ---"
else
  PROXY_DOMAIN="sec.cse.csusb.edu"
  SKIP_APACHE=false
fi

PROXY_PATH="/team1f25"  # public prefix (leading slash, no trailing slash)
SSL_SEARCH_STRING="SSLCertificateFile /etc/letsencrypt/live/${PROXY_DOMAIN}/"
SITES_AVAILABLE_DIR="/etc/apache2/sites-available"

# --- Docker Build & Run ---
echo "--- Starting Docker application management ---"

if [ ! -d "$DOCKER_WORKDIR" ]; then
  echo "Error: Directory '$DOCKER_WORKDIR' not found. Exiting."
  exit 1
fi

cd "$DOCKER_WORKDIR"

echo "🧹 Cleaning old container(s) and image..."
# Remove the named container if it exists
docker rm -f "$DOCKER_CONTAINER_NAME" >/dev/null 2>&1 || true

# Remove any containers created from the image (if any)
ids="$(docker ps -aq --filter ancestor="$DOCKER_APP_IMAGE" || true)"
if [ -n "${ids}" ]; then
  docker rm -f ${ids} >/dev/null 2>&1 || true
fi

# Remove the image if it exists
docker rmi -f "$DOCKER_APP_IMAGE" >/dev/null 2>&1 || true

echo "🔨 Building image $DOCKER_APP_IMAGE..."
docker build -t "$DOCKER_APP_IMAGE" .

echo "🚀 Running container $DOCKER_CONTAINER_NAME on :$DOCKER_APP_PORT..."
docker run -d --restart unless-stopped \
  --name "$DOCKER_CONTAINER_NAME" \
  -p "$DOCKER_APP_PORT":"$DOCKER_APP_PORT" \
  "$DOCKER_APP_IMAGE":latest

echo "✅ Docker setup complete."
cd - >/dev/null 2>&1  # Return to the original directory quietly

# --- Apache Reverse Proxy Configuration (Conditional) ---
if [ "$SKIP_APACHE" = "false" ]; then
  # Root privileges are only required for Apache config/reload.
  if [ "$EUID" -ne 0 ]; then
    echo "Error: Apache configuration requires root. Please run with sudo."
    exit 1
  fi

  echo "--- Starting Apache configuration update ---"
  echo "--- Searching for existing HTTPS VirtualHost file for $PROXY_DOMAIN ---"
  CONFIG_FILE="$(grep -l -R "$SSL_SEARCH_STRING" "$SITES_AVAILABLE_DIR" 2>/dev/null | head -n 1)"

  if [ -z "${CONFIG_FILE}" ]; then
    echo "Error: Could not find an existing Apache HTTPS VirtualHost file for $PROXY_DOMAIN."
    echo "Please ensure Certbot has been run for this domain. Exiting without modifying Apache."
    exit 1
  fi
  echo "Found configuration file: $CONFIG_FILE"

  echo "--- Enabling required Apache modules ---"
  a2enmod proxy proxy_http proxy_wstunnel rewrite headers ssl >/dev/null

  echo "--- Checking and adding reverse proxy rules to $CONFIG_FILE ---"
  if grep -q "Streamlit reverse proxy for team1f25" "$CONFIG_FILE"; then
    echo "Configuration for Streamlit already exists. Showing current block:"
    sed -n '/# --- Streamlit reverse proxy for team1f25 ---/,/# --- End Streamlit reverse proxy for team1f25 ---/p' "$CONFIG_FILE"
  else
    echo "Configuration not found. Appending to file."
    cat <<EOF >> "$CONFIG_FILE"

  # --- Streamlit reverse proxy for team1f25 ---
  # Reverse proxy + websocket support for Streamlit at ${PROXY_PATH}
  ProxyRequests Off

  <Proxy "*">
      Require all granted
  </Proxy>

  RewriteEngine On

  # Normalize missing trailing slash: /team1f25 -> /team1f25/
  RewriteRule ^${PROXY_PATH}\$ ${PROXY_PATH}/ [R=301,L]

  # Core HTTP proxy (TRAILING SLASHES ARE IMPORTANT)
  ProxyPass        ${PROXY_PATH}/ http://localhost:${DOCKER_APP_PORT}${PROXY_PATH}/ retry=0 keepalive=On
  ProxyPassReverse ${PROXY_PATH}/ http://localhost:${DOCKER_APP_PORT}${PROXY_PATH}/

  # WebSocket upgrade for Streamlit
  RewriteCond %{HTTP:Upgrade} =websocket [NC]
  RewriteCond %{HTTP:Connection} upgrade [NC]
  RewriteRule ^${PROXY_PATH}/(.*) ws://localhost:${DOCKER_APP_PORT}${PROXY_PATH}/\$1 [P,L]

  # Preserve scheme info for the app
  RequestHeader set X-Forwarded-Proto "https"
  # --- End Streamlit reverse proxy for team1f25 ---
EOF
  fi

  echo "--- Testing Apache configuration syntax ---"
  if ! apachectl configtest &>/dev/null; then
    echo "Error: Apache configuration test failed. Reverting appended changes."
    # Remove everything from our start marker to the end of the file
    sed -i '/# --- Streamlit reverse proxy for team1f25 ---/,$d' "$CONFIG_FILE"
    echo "Changes reverted. Exiting."
    exit 1
  else
    echo "Syntax OK."
  fi

  echo "--- Reloading Apache service to apply changes ---"
  systemctl reload apache2

  echo "✅ Apache setup complete."
  echo "✅ The Streamlit proxy configuration has been added to your HTTPS VirtualHost."
fi

# --- Final Confirmation ---
if [ "$PROXY_DOMAIN" = "localhost" ]; then
  echo "✅ Local deployment complete. Your application is available at:"
  echo "   http://localhost:${DOCKER_APP_PORT}${PROXY_PATH}/"
else
  echo "✅ Remote deployment complete. Your application is available at:"
  echo "   https://${PROXY_DOMAIN}${PROXY_PATH}/"
fi
