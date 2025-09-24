#!/usr/bin/env bash
set -euo pipefail

# --- Paths ---
SITES_DIR="/etc/apache2/sites-available"
NEW_BLOCK_FILE="./apache-proxy.conf"

# --- Helpers ---
require_root() {
  if [[ ${EUID} -ne 0 ]]; then
    echo "Please run as root (sudo)." >&2
    exit 1
  fi
}

install_deps() {
  if command -v apt-get >/dev/null 2>&1; then
    apt-get update -y
    apt-get install -y apache2 apache2-utils perl grep coreutils
  fi
}

ensure_tools() {
  for cmd in perl grep cp date apachectl systemctl a2enmod; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
      echo "Missing required command: $cmd" >&2
      exit 127
    fi
  done
}

read_new_block() {
  if [[ ! -f "$NEW_BLOCK_FILE" || ! -s "$NEW_BLOCK_FILE" ]]; then
    echo "Error: New block file '$NEW_BLOCK_FILE' not found or empty." >&2
    exit 1
  fi
}

backup_file() {
  local file="$1"
  local ts
  ts="$(date +%Y%m%d-%H%M%S)"
  cp -p -- "$file" "${file}.bak.${ts}"
  echo "  ↳ Backup: ${file}.bak.${ts}"
}

replace_vhost_block_in_file() {
  local file="$1"
  NEW_PATH="$NEW_BLOCK_FILE" \
  perl -0777 -i -pe '
    BEGIN {
      sub slurp {
        my ($p) = @_;
        open my $fh, "<", $p or die "Cannot open $p: $!";
        local $/; <$fh>
      }
      $new = slurp($ENV{NEW_PATH});

      # Escape replacement metachars so they stay literal in the file
      $new =~ s/\\/\\\\/g;   # backslashes
      $new =~ s/\$/\$\$/g;   # dollar signs ($1 etc.)
    }

    # Replace ALL 443 vhost blocks in this file.
    # If you want ONLY the first one, change s///g to s/// (no g).
    s!<VirtualHost\s+\*:443\b>.*?</VirtualHost>!$new!gs;
  ' -- "$file"
}

enable_modules() {
  a2enmod ssl >/dev/null 2>&1 || true
  a2enmod proxy >/dev/null 2>&1 || true
  a2enmod proxy_http >/dev/null 2>&1 || true
  a2enmod proxy_wstunnel >/dev/null 2>&1 || true
  a2enmod headers >/dev/null 2>&1 || true
  a2enmod rewrite >/dev/null 2>&1 || true
}

validate_and_reload() {
  echo "🔎 apachectl configtest..."
  if apachectl configtest; then
    echo "✅ Config OK. Reloading Apache..."
    systemctl reload apache2 || {
      echo "Reload failed; trying restart..."
      systemctl restart apache2
    }
    echo "✅ Apache reloaded."
  else
    echo "❌ Config test failed. Backups were kept. No reload performed." >&2
    exit 1
  fi
}

main() {
  require_root
  install_deps
  ensure_tools
  read_new_block

  echo "🔎 Searching for files with '<VirtualHost *:443>' under: $SITES_DIR"
  mapfile -t candidates < <(grep -rlE -- '<VirtualHost[[:space:]]+\*:443>' "$SITES_DIR" || true)

  if [[ ${#candidates[@]} -eq 0 ]]; then
    echo "No files with a '<VirtualHost *:443>' block were found in $SITES_DIR."
    exit 0
  fi

  local changed=false
  for f in "${candidates[@]}"; do
    if perl -0777 -ne 'print 1 if /<VirtualHost\s+\*:443\b>.*?<\/VirtualHost>/s' -- "$f" >/dev/null 2>&1; then
      echo "🧩 Updating: $f"
      backup_file "$f"
      replace_vhost_block_in_file "$f"
      changed=true
    fi
  done

  if [[ "$changed" == "false" ]]; then
    echo "No <VirtualHost *:443> blocks found to replace. Nothing changed."
    exit 0
  fi

  enable_modules
  validate_and_reload
}

main "$@"
