#!/usr/bin/env bash
# scripts/caddy-ca-trust-macos.sh — D-17-115 Phase 1 (WP-04 macOS automation)
#
# Imports the Caddy internal root CA into the System keychain and marks it
# as trusted for SSL ("trustRoot"). Idempotent: skips re-install if a
# certificate matching "Caddy Local Authority" is already present in the
# System keychain.
#
# Prerequisites:
#   - Caddy root CA committed at deployment/caddy/internal-root.crt
#     (deferred to Phase 2 of D-17-115; cert extraction requires on-LAN
#     access to Mac Mini 192.168.10.145 — see
#     docs/runbooks/caddy-internal-ca-trust.md §"Cert provenance").
#   - macOS (Darwin) host. Linux distribution is a separate deliverable
#     deferred until Threadripper / Ryzen OS is confirmed.
#   - sudo available; keychain modification requires admin password.
#
# Usage:
#   ./scripts/caddy-ca-trust-macos.sh                        # default cert path
#   ./scripts/caddy-ca-trust-macos.sh /path/to/root.crt      # explicit cert path
#
# Exit codes:
#   0  trust install succeeded OR cert already trusted (idempotent no-op)
#   1  generic failure
#   2  cert file not found at the expected path
#   3  not running on macOS (uname -s != Darwin)
#   4  sudo not available in PATH
#   5  post-install verification failed (cert not in System keychain after install)
#
# Cross-references:
#   D-17-115 (docs/PROJECT_FRAMEWORK.md §9)
#   docs/runbooks/caddy-internal-ca-trust.md
#   docs/architecture-facts/caddy-internal-tls-doctrine.md
#   docs/known-issues/KI-012-caddy-ca-rotation.md (~10-year rotation tracking)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

DEFAULT_CERT_PATH="$REPO_ROOT/deployment/caddy/internal-root.crt"
CERT_PATH="${1:-$DEFAULT_CERT_PATH}"
SYSTEM_KEYCHAIN="/Library/Keychains/System.keychain"
CERT_CN_SUBSTR="Caddy Local Authority"

# Pre-flight: macOS only.
if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Error: script is macOS-only (uname -s reports '$(uname -s)'). Linux support is a separate deliverable." >&2
  exit 3
fi

# Pre-flight: sudo available.
if ! command -v sudo >/dev/null 2>&1; then
  echo "Error: sudo not found in PATH. Keychain modification requires admin password." >&2
  exit 4
fi

# Pre-flight: cert file exists. If not, point the operator at the extraction procedure.
if [[ ! -f "$CERT_PATH" ]]; then
  cat >&2 <<EOF
Error: Caddy root CA not found at $CERT_PATH

The cert file must be extracted from the Caddy container on Mac Mini and
committed to the repo before this script can run. Extraction procedure:

  docker exec caddy cat /data/caddy/pki/authorities/local/root.crt > $CERT_PATH

See docs/runbooks/caddy-internal-ca-trust.md §"Cert provenance" for the full
procedure including SHA-256 fingerprint capture and issuer-DN recording.

D-17-115 Phase 2 (next on-LAN session) will commit the cert file. Until then,
this script's pre-flight intentionally fails fast rather than guessing.
EOF
  exit 2
fi

# Idempotency check: is a "Caddy Local Authority" cert already in the System keychain?
if sudo security find-certificate -a -c "$CERT_CN_SUBSTR" "$SYSTEM_KEYCHAIN" >/dev/null 2>&1; then
  echo "Caddy root CA already trusted on this device (System keychain has a matching '$CERT_CN_SUBSTR' certificate)."
  echo "If you want to force re-import (e.g. after CA rotation per KI-012), remove the existing cert first via Keychain Access."
  exit 0
fi

# Surface cert details before invoking sudo so the operator sees what they're approving.
echo "Importing Caddy root CA from: $CERT_PATH"
echo ""
echo "Cert details (subject / issuer / SHA-256 fingerprint):"
openssl x509 -in "$CERT_PATH" -noout -subject -issuer -fingerprint -sha256 || true
echo ""
echo "About to invoke:"
echo "  sudo security add-trusted-cert -d -r trustRoot -k $SYSTEM_KEYCHAIN $CERT_PATH"
echo "macOS will prompt for your admin password."
echo ""

# Main action.
sudo security add-trusted-cert -d -r trustRoot -k "$SYSTEM_KEYCHAIN" "$CERT_PATH"

# Post-install verification.
if ! sudo security find-certificate -a -c "$CERT_CN_SUBSTR" "$SYSTEM_KEYCHAIN" >/dev/null 2>&1; then
  echo "Error: post-install verification failed — cert not found in System keychain after install." >&2
  echo "Run 'sudo security find-certificate -a -c \"$CERT_CN_SUBSTR\" $SYSTEM_KEYCHAIN' manually to diagnose." >&2
  exit 5
fi

echo ""
echo "Caddy root CA installed and trusted on this device."
echo "Verify: open https://vault.internal/ in a browser — should load without certificate warnings."
