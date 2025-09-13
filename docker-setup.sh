#!/usr/bin/env bash
set -Eeuo pipefail  # -E so ERR trap fires in functions/subshells

# ---------- error handling ----------
FAILED=0
on_error() {
  local exit_code="$1"
  local line_no="$2"
  local cmd="$3"
  FAILED=1
  echo ""
  echo "❌ ERROR: Command failed (exit ${exit_code})"
  echo "   at ${BASH_SOURCE[1]}:${line_no}"
  echo "   → ${cmd}"
}
on_exit() {
  if [[ "$FAILED" -eq 1 ]]; then
    echo ""
    echo "💥 Script aborted due to the error above."
  fi
}
trap 'on_error $? $LINENO "$BASH_COMMAND"' ERR
trap 'on_exit' EXIT
# ------------------------------------

# Default mode: prod (use real certs and port 443)
MODE="${1:-prod}"

# Paths relative to this script
cd "$(dirname "$0")"

DOMAIN_LOCAL="localhost"
DOMAIN_PROD="sec.cse.csusb.edu"

case "$MODE" in
  prod)
    HTTPS_PORT="443"
    CERT_SUBDIR="prod"
    CN="$DOMAIN_PROD"
    ;;
  local)
    HTTPS_PORT="2501"
    CERT_SUBDIR="local"
    CN="$DOMAIN_LOCAL"
    ;;
  *)
    echo "Usage: $0 [prod|local]"
    exit 1
    ;;
esac

echo "🛑 Stopping any existing containers..."
docker compose down --remove-orphans

CERT_DIR="apache/certs/${CERT_SUBDIR}"
CRT="${CERT_DIR}/server.crt"
KEY="${CERT_DIR}/server.key"
mkdir -p "$CERT_DIR"

if [[ "$MODE" == "local" ]]; then
  echo "🗑️  Resetting local self-signed certs..."
  rm -f "$CRT" "$KEY"

  echo "🔐 Generating LOCAL self-signed certificate (CN=${CN}) with SAN..."
  # Build a minimal OpenSSL config with SANs (works across OpenSSL/LibreSSL)
  umask 077
  CONF="${CERT_DIR}/openssl-local.cnf"

  ALT_NAMES="DNS.1 = ${CN}"
  if [[ "$CN" == "localhost" ]]; then
    ALT_NAMES+=$'\n''IP.1 = 127.0.0.1'
    ALT_NAMES+=$'\n''IP.2 = ::1'
  fi

  cat > "$CONF" <<EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
x509_extensions = req_ext
distinguished_name = dn

[dn]
C = US
ST = California
L = San Bernardino
O = CSUSB
CN = ${CN}

[req_ext]
subjectAltName = @alt_names

[alt_names]
${ALT_NAMES}
EOF

  # Don't silence errors; let traps print exact failure if any
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$KEY" -out "$CRT" -sha256 \
    -config "$CONF" -extensions req_ext

  chmod 600 "$KEY"
else
  # PROD: require real certs present
  if [[ ! -f "$CRT" || ! -f "$KEY" ]]; then
    echo "❌ Missing PRODUCTION certs in ${CERT_DIR}."
    echo "   Place your FULL CHAIN cert as:"
    echo "     ${CRT}"
    echo "   and private key as:"
    echo "     ${KEY}"
    echo "   Then re-run: $0"
    exit 2
  fi
fi

echo "🔨 Building fresh images..."
docker compose build --no-cache

echo "🚀 Starting services (mode=${MODE}, https port=${HTTPS_PORT}, cert dir=${CERT_SUBDIR})..."
HTTPS_PORT="${HTTPS_PORT}" CERT_DIR="${CERT_SUBDIR}" docker compose up -d

echo
echo "✅ Setup complete. Services are running."
echo
if [[ "$MODE" == "local" ]]; then
  echo "Open:"
  echo "  • App:     https://localhost:${HTTPS_PORT}/team1f25/"
  echo "  • Jupyter: https://localhost:${HTTPS_PORT}/team1f25/jupyter/"
else
  echo "Open:"
  echo "  • App:     https://${DOMAIN_PROD}/team1f25/"
  echo "  • Jupyter: https://${DOMAIN_PROD}/team1f25/jupyter/"
fi

echo
echo "ℹ️  Logs:    docker compose logs -f proxy"
