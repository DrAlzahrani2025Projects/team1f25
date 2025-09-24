#!/usr/bin/env bash
set -euo pipefail

# --- Paths & Inputs ---
SITES_DIR="/etc/apache2/sites-available"
NEW_BLOCK_443="./apache-proxy-https.conf"
NEW_BLOCK_80="./apache-proxy-http.conf"

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

check_file_nonempty() {
  local p="$1"
  if [[ ! -f "$p" || ! -s "$p" ]]; then
    echo "Error: Required file '$p' not found or empty." >&2
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

# Replace <VirtualHost *:<port> ... </VirtualHost> blocks with the contents of new_path.
# Escapes '\' and '$' in replacement so RewriteRule $1 etc. remain intact.  (Fix for issue #1)
# Pattern allows extra attributes after the port and flexible whitespace.  (Part of issue #6 hardening)
replace_vhost_block_in_file() {
  local file="$1"
  local port="$2"
  local new_path="$3"
  local first_only="${4:-false}"

  NEW_PATH="$new_path" PORT="$port" FIRST_ONLY="$first_only" \
  perl -0777 -i -pe '
    BEGIN {
      sub slurp {
        my ($p) = @_;
        open my $fh, "<", $p or die "Cannot open $p: $!";
        local $/; <$fh>
      }
      my $new = slurp($ENV{NEW_PATH});

      # --- FIX #1: Escape replacement metachars so Apache text stays literal
      $new =~ s/\\/\\\\/g;   # escape backslashes
      $new =~ s/\$/\$\$/g;   # escape dollars ($1 etc.)

      # Tolerant pattern: allow attrs/whitespace after the port and before '>'
      our $pat = qr{<VirtualHost\s+\*:\Q$ENV{PORT}\E\b[^>]*>.*?</VirtualHost>}s;

      # Stash for use in s///e below
      our $REPL = $new;
    }

    # Replace first or all matches depending on flag
    if ($ENV{FIRST_ONLY} && $ENV{FIRST_ONLY} eq "true") {
      s/$pat/$REPL/s;
    } else {
      s/$pat/$REPL/gs;
    }
  ' -- "$file"
}

# Does file contain a vhost for the given port? (tolerant pattern; part of issue #6 hardening)
has_vhost_for_port() {
  local file="$1" port="$2"
  perl -0777 -ne 'exit(0) if /<VirtualHost\s+\*:'"$port"'\b[^>]*>.*?<\/VirtualHost>/s; exit(1);' -- "$file"
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
    systemctl reload apache2 2>/dev/null || service apache2 reload
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
  check_file_nonempty "$NEW_BLOCK_443"
  check_file_nonempty "$NEW_BLOCK_80"

  # --- ISSUE #6: More tolerant candidate search (attrs/whitespace allowed)
  echo "🔎 Searching for files with '<VirtualHost *:443>' under: $SITES_DIR"
  mapfile -t candidates_443 < <(grep -rlE -- '<VirtualHost[[:space:]]+\*:443\b[^>]*>' "$SITES_DIR" || true)

  local changed=false

  if [[ ${#candidates_443[@]} -gt 0 ]]; then
    for f in "${candidates_443[@]}"; do
      if has_vhost_for_port "$f" 443; then
        echo "🧩 Updating 443 vhost in: $f"
        backup_file "$f"
        replace_vhost_block_in_file "$f" 443 "$NEW_BLOCK_443" "false"
        changed=true
      fi
    done
  fi

  # If no 443 blocks actually changed, fallback to :80 even if 443 tags exist but didn't match exact pattern (issue #6)
  if [[ "$changed" == "false" ]]; then
    echo "ℹ️  No 443 vhost blocks updated. Falling back to search for '<VirtualHost *:80>'."
    mapfile -t candidates_80 < <(grep -rlE -- '<VirtualHost[[:space:]]+\*:80\b[^>]*>' "$SITES_DIR" || true)
    if [[ ${#candidates_80[@]} -eq 0 ]]; then
      echo "No files with a '<VirtualHost *:80>' block were found in $SITES_DIR."
      exit 0
    fi
    for f in "${candidates_80[@]}"; do
      if has_vhost_for_port "$f" 80; then
        echo "🧩 Updating 80 vhost in: $f"
        backup_file "$f"
        replace_vhost_block_in_file "$f" 80 "$NEW_BLOCK_80" "false"
        changed=true
      fi
    done
  fi

  if [[ "$changed" == "false" ]]; then
    echo "No <VirtualHost *:443> or <VirtualHost *:80> blocks found to replace. Nothing changed."
    exit 0
  fi

  enable_modules
  validate_and_reload
}

main "$@"
