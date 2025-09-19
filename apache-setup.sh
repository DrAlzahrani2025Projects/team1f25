#!/usr/bin/env bash
set -euo pipefail

# --- Apache Configuration ---
PROXY_DOMAIN="sec.cse.csusb.edu"
PROXY_PATH="/team1f25"
DOCKER_APP_PORT="5001"
SSL_SEARCH_STRING="SSLCertificateFile /etc/letsencrypt/live/${PROXY_DOMAIN}/"
SITES_AVAILABLE_DIR="/etc/apache2/sites-available"

# Must be root
if [ "$EUID" -ne 0 ]; then
  echo "Error: Apache configuration requires root. Please run with sudo."
  exit 1
fi

echo "--- Starting Apache configuration update ---"

CONFIG_FILE="$(grep -l -R "$SSL_SEARCH_STRING" "$SITES_AVAILABLE_DIR" 2>/dev/null | head -n 1)"
if [ -z "${CONFIG_FILE}" ]; then
  echo "Error: Could not find an existing Apache HTTPS VirtualHost file for $PROXY_DOMAIN."
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
  ProxyRequests Off

  <Proxy "*">
      Require all granted
  </Proxy>

  RewriteEngine On
  RewriteRule ^${PROXY_PATH}\$ ${PROXY_PATH}/ [R=301,L]

  ProxyPass        ${PROXY_PATH}/ http://localhost:${DOCKER_APP_PORT}${PROXY_PATH}/ retry=0 keepalive=On
  ProxyPassReverse ${PROXY_PATH}/ http://localhost:${DOCKER_APP_PORT}${PROXY_PATH}/

  RewriteCond %{HTTP:Upgrade} =websocket [NC]
  RewriteCond %{HTTP:Connection} upgrade [NC]
  RewriteRule ^${PROXY_PATH}/(.*) ws://localhost:${DOCKER_APP_PORT}${PROXY_PATH}/\$1 [P,L]

  RequestHeader set X-Forwarded-Proto "https"
  # --- End Streamlit reverse proxy for team1f25 ---
EOF
fi

echo "--- Testing Apache configuration syntax ---"
if ! apachectl configtest &>/dev/null; then
  echo "Error: Apache configuration test failed. Reverting appended changes."
  sed -i '/# --- Streamlit reverse proxy for team1f25 ---/,$d' "$CONFIG_FILE"
  exit 1
else
  echo "Syntax OK."
fi

echo "--- Reloading Apache service ---"
systemctl reload apache2

echo "✅ Apache setup complete. App accessible at https://${PROXY_DOMAIN}${PROXY_PATH}/"
