#!/usr/bin/env bash
set -euo pipefail

# -- Paths & Inputs --
SITES_DIR="/etc/apache2/sites-available"
NEW_BLOCK_443="./apache-proxy-https.conf"
NEW_BLOCK_80="./apache-proxy-http.conf"

declare -a BACKUPS=()

# -- Helpers --
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
  if command -v apachectl >/dev/null 2>&1; then
    export APCTL="apachectl"
  elif command -v apache2ctl >/dev/null 2>&1; then
    export APCTL="apache2ctl"
  else
    echo "Missing required command: apachectl or apache2ctl" >&2
    exit 127
  fi

  for cmd in perl grep cp date a2enmod; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
      echo "Missing required command: $cmd" >&2
      exit 127
    fi
  done

  if ! command -v systemctl >/dev/null 2>&1 && ! command -v service >/dev/null 2>&1; then
    echo "Neither systemctl nor service is available to reload apache2." >&2
    exit 127
  fi
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
  local bkp="${file}.bak.${ts}"
  cp -p -- "$file" "$bkp"
  BACKUPS+=("$bkp")
  echo "  ↳ Backup: $bkp"
}

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
      $new =~ s/\\/\\\\/g;
      $new =~ s/\$/\$\$/g;

      our $pat = qr{<VirtualHost\s+\*:\Q$ENV{PORT}\E\b[^>]*>.*?</VirtualHost>}si;
      our $REPL = $new;
      our $COUNT = 0;
    }

    if ($ENV{FIRST_ONLY} && $ENV{FIRST_ONLY} eq "true") {
      $COUNT += (s/$pat/$REPL/s);
    } else {
      $COUNT += (s/$pat/$REPL/gs);
    }

    END { print "REPLACED:$COUNT\n"; }
  ' -- "$file"
}

has_vhost_for_port() {
  local file="$1" port="$2"
  perl -0777 -ne 'exit(0) if /<VirtualHost\s+\*:'"$port"'\b[^>]*>.*?<\/VirtualHost>/si; exit(1);' -- "$file"
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
  echo "🔎 $APCTL configtest..."
  if "$APCTL" configtest; then
    echo "✅ Config OK. Reloading Apache..."
    if command -v systemctl >/dev/null 2>&1; then
      systemctl reload apache2
    elif command -v service >/dev/null 2>&1; then
      service apache2 reload
    fi
    echo "✅ Apache reloaded."

    # --- NEW: cleanup backups after success
    if [[ ${#BACKUPS[@]} -gt 0 ]]; then
      echo "🧹 Cleaning up backups..."
      for b in "${BACKUPS[@]}"; do
        rm -f -- "$b"
        echo "  ✗ Removed $b"
      done
    fi
  else
    echo "❌ Config test failed. Restoring backups..."
    for b in "${BACKUPS[@]}"; do
      orig="${b%".bak."*}"
      echo "  ↩ Restoring $orig from $b"
      cp -f -- "$b" "$orig"
    done
    echo "⚠️  Config restored to previous state. No reload performed."
    exit 1
  fi
}

main() {
  require_root
  install_deps
  ensure_tools
  check_file_nonempty "$NEW_BLOCK_443"
  check_file_nonempty "$NEW_BLOCK_80"

  if [[ ! -d "$SITES_DIR" ]]; then
    echo "Directory $SITES_DIR not found." >&2
    exit 1
  fi

  echo "🔎 Searching for files with '<VirtualHost *:443>' under: $SITES_DIR"
  mapfile -t candidates_443 < <(grep -rilE -- '<VirtualHost[[:space:]]+\*:443\b[^>]*>' "$SITES_DIR" || true)

  local changed=false

  if [[ ${#candidates_443[@]} -gt 0 ]]; then
    for f in "${candidates_443[@]}"; do
      if has_vhost_for_port "$f" 443; then
        echo "🧩 Updating 443 vhost in: $f"
        backup_file "$f"
        out="$(replace_vhost_block_in_file "$f" 443 "$NEW_BLOCK_443" "false")"
        echo "  $out"
        if [[ "$out" =~ REPLACED:([0-9]+) ]] && (( ${BASH_REMATCH[1]} > 0 )); then
          changed=true
        fi
      fi
    done
  fi

  if [[ "$changed" == "false" ]]; then
    echo "ℹ️  No 443 vhost blocks updated. Falling back to search for '<VirtualHost *:80>'."
    mapfile -t candidates_80 < <(grep -rilE -- '<VirtualHost[[:space:]]+\*:80\b[^>]*>' "$SITES_DIR" || true)
    if [[ ${#candidates_80[@]} -eq 0 ]]; then
      echo "No files with a '<VirtualHost *:80>' block were found in $SITES_DIR."
      exit 0
    fi
    for f in "${candidates_80[@]}"; do
      if has_vhost_for_port "$f" 80; then
        echo "🧩 Updating 80 vhost in: $f"
        backup_file "$f"
        out="$(replace_vhost_block_in_file "$f" 80 "$NEW_BLOCK_80" "false")"
        echo "  $out"
        if [[ "$out" =~ REPLACED:([0-9]+) ]] && (( ${BASH_REMATCH[1]} > 0 )); then
          changed=true
        fi
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
