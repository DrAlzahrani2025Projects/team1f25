#!/usr/bin/env bash
set -euo pipefail

# --- Apache Configuration ---
PROXY_DOMAIN="sec.cse.csusb.edu"
PROXY_PATH="/team1f25"
DOCKER_APP_PORT="5001"

SITES_AVAILABLE_DIR="/etc/apache2/sites-available"

# Path to the new configuration block file
NEW_BLOCK_FILE="./apache-proxy-team1f25.conf"

# Must be root for a2enmod / editing vhost / reload
if [ "$EUID" -ne 0 ]; then
  echo "Error: Apache configuration requires root. Please run with sudo."
  exit 1
fi

echo "--- Locating HTTPS VirtualHost for ${PROXY_DOMAIN} ---"
CONFIG_FILE="$(grep -l -R "${PROXY_PATH}" "$SITES_AVAILABLE_DIR" 2>/dev/null | head -n 1)"
if [ -z "${CONFIG_FILE}" ]; then
  echo "Error: Could not find an Apache HTTPS VirtualHost file for ${PROXY_DOMAIN} with path ${PROXY_PATH}."
  echo "Ensure certs exist and the vhost is under ${SITES_AVAILABLE_DIR}."
  exit 1
fi
echo "Found: ${CONFIG_FILE}"

echo "--- Enabling required Apache modules ---"
a2enmod proxy proxy_http proxy_wstunnel rewrite headers ssl >/dev/null

# Read the content of the new block from the external file
if [ ! -f "${NEW_BLOCK_FILE}" ]; then
  echo "Error: Configuration file not found: ${NEW_BLOCK_FILE}"
  exit 1
fi
# Using mapfile to read the file contents correctly into an array
mapfile -t NEW_BLOCK_ARRAY < "${NEW_BLOCK_FILE}"
# Join the array elements with newlines to form a single string
NEW_BLOCK=$(printf "%s\n" "${NEW_BLOCK_ARRAY[@]}")

# Define the backup filename here, after CONFIG_FILE is found
BACKUP_FILE="${CONFIG_FILE}.bak.$(date +%Y%m%d-%H%M%S)"

echo "--- Backing up vhost file ---"
cp -a "${CONFIG_FILE}" "${BACKUP_FILE}"

LEGACY_HEADER_LINE='########################################'
LEGACY_TITLE_LINE='# Streamlit reverse proxy for team1f25'
NEW_MARKER='# --- Streamlit reverse proxy for team1f25 ---'

# Use a flag to track if a successful replacement occurred
REPLACEMENT_SUCCESSFUL=0

if grep -qF "${NEW_MARKER}" "${CONFIG_FILE}"; then
  echo "New-style block already present. Updating it in-place…"
  # Replace everything between our start/end markers with NEW_BLOCK

  sed -i '/^# --- Streamlit reverse proxy for team1f25 ---/,/^# --- End Streamlit reverse proxy for team1f25 ---/d' "${CONFIG_FILE}"

  echo "" >> "${CONFIG_FILE}"
  echo "${NEW_BLOCK}" >> "${CONFIG_FILE}"
  REPLACEMENT_SUCCESSFUL=1
elif grep -qF "${LEGACY_TITLE_LINE}" "${CONFIG_FILE}"; then
  echo "Legacy block detected. Removing it before inserting the new block…"

  # Remove the old block first, including the start and end marker lines.
  # This will delete everything from the first "########################################" to the last one.
  sed -i '/^########################################/,/^########################################/d' "${CONFIG_FILE}"

  # Now append the new block
  echo "" >> "${CONFIG_FILE}"
  echo "${NEW_BLOCK}" >> "${CONFIG_FILE}"
  REPLACEMENT_SUCCESSFUL=1
else
  echo "Inserting new block…"
  echo "" >> "${CONFIG_FILE}"
  echo "${NEW_BLOCK}" >> "${CONFIG_FILE}"
  REPLACEMENT_SUCCESSFUL=1
fi

# Remove the backup if the replacement was successful.
if [ "$REPLACEMENT_SUCCESSFUL" -eq 1 ]; then
  echo "--- Configuration updated successfully. Removing backup file ---"
  rm "${BACKUP_FILE}"
else
  echo "--- Configuration not updated. Backup file retained for safety ---"
fi

echo "--- Gracefully reloading Apache ---"
apachectl -k graceful

echo "--- Script complete ---"
