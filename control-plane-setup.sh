#!/usr/bin/env bash
# =============================================================
# control-plane one-shot setup for 192.168.10.201 (qnap-brain)
# Run via: bash control-plane-setup.sh
# =============================================================
CONTROL_PLANE_HOME="${CONTROL_PLANE_HOME:-$HOME/control-plane}"
set -euo pipefail

echo "[1/4] Creating directory structure..."
mkdir -p $CONTROL_PLANE_HOME/config \
         $CONTROL_PLANE_HOME/secrets \
         $CONTROL_PLANE_HOME/adapters \
         $CONTROL_PLANE_HOME/workflows \
         $CONTROL_PLANE_HOME/core \
         $CONTROL_PLANE_HOME/artifacts \
         $CONTROL_PLANE_HOME/logs \
         $CONTROL_PLANE_HOME/scripts \
         $CONTROL_PLANE_HOME/tests

echo "[2/4] Writing config/endpoints.yaml..."
cat > $CONTROL_PLANE_HOME/config/endpoints.yaml <<'EOF'
control_plane:
  name: qnap-brain
  host: 192.168.10.201
  role: automation_control_plane
  read_only_phase: true
qnap_201:
  enabled: true
  adapter: qnap_readonly
  base_url: https://192.168.10.201
  verify_tls: false
  auth:
    type: qnap_web_login
    username_env: QNAP201_USERNAME
    password_env: QNAP201_PASSWORD
  capabilities:
    - qts_reachability
    - qts_login_check
    - container_station_visibility
    - screenshot_capture
sonarr:
  enabled: true
  adapter: sonarr_readonly
  base_url: http://192.168.10.201:8989
  verify_tls: false
  auth:
    type: api_key_header
    header_name: X-Api-Key
    api_key_env: SONARR_API_KEY
  endpoints:
    system_status: /api/v3/system/status
    health: /api/v3/health
    rootfolder: /api/v3/rootfolder
    qualityprofile: /api/v3/qualityprofile
    downloadclient: /api/v3/downloadclient
    indexer: /api/v3/indexer
    remotepathmapping: /api/v3/remotepathmapping
    queue: /api/v3/queue
    wanted_missing: /api/v3/wanted/missing
radarr:
  enabled: true
  adapter: radarr_readonly
  base_url: http://192.168.10.201:7878
  verify_tls: false
  auth:
    type: api_key_header
    header_name: X-Api-Key
    api_key_env: RADARR_API_KEY
  endpoints:
    system_status: /api/v3/system/status
    health: /api/v3/health
    rootfolder: /api/v3/rootfolder
    qualityprofile: /api/v3/qualityprofile
    downloadclient: /api/v3/downloadclient
    indexer: /api/v3/indexer
    remotepathmapping: /api/v3/remotepathmapping
    queue: /api/v3/queue
    wanted_cutoff: /api/v3/wanted/cutoff
sportarr:
  enabled: true
  adapter: sportarr_readonly
  base_url: http://192.168.10.201:1867
  verify_tls: false
  auth:
    type: api_key_header
    header_name: X-Api-Key
    api_key_env: SPORTARR_API_KEY
  endpoints:
    system_status: /api/system/status
    health: /api/system/health
    rootfolder: /api/rootfolder
    downloadclient: /api/downloadclient
    indexer: /api/indexer
    remotepathmapping: /api/remotepathmapping
    queue: /api/queue
    history: /api/history
  notes:
    - known_rtorrent_test_bug_false_positive
prowlarr:
  enabled: true
  adapter: prowlarr_readonly
  base_url: http://192.168.10.201:9696
  verify_tls: false
  auth:
    type: api_key_header
    header_name: X-Api-Key
    api_key_env: PROWLARR_API_KEY
  endpoints:
    system_status: /api/v1/system/status
    health: /api/v1/health
    indexer: /api/v1/indexer
    applications: /api/v1/applications
    tag: /api/v1/tag
    downloadclient: /api/v1/downloadclient
    history: /api/v1/history
plex:
  enabled: true
  adapter: plex_readonly
  base_url: http://192.168.10.201:32400
  verify_tls: false
  auth:
    type: token_header
    header_name: X-Plex-Token
    token_env: PLEX_TOKEN
    accept_header: application/json
  endpoints:
    library_sections: /library/sections
    sessions: /status/sessions
    prefs: /:/prefs
    hubs: /hubs
  known_paths:
    movies: /share/CACHEDEV2_DATA/download/Movies
    tv: /share/CACHEDEV2_DATA/download/TV
    sports: /share/CACHEDEV2_DATA/download2/download/Sports
seedbox_rtorrent:
  enabled: true
  adapter: seedbox_readonly
  base_url: https://5.nl19.seedit4.me
  verify_tls: true
  auth:
    type: basic_auth
    username_env: SEEDBOX_USERNAME
    password_env: SEEDBOX_PASSWORD
  endpoints:
    rutorrent_rpc: /rutorrent/plugins/httprpc/action.php
  paths:
    remote_root: /home/seedit4me/torrents/rtorrent/
seedbox_sabnzbd:
  enabled: true
  adapter: seedbox_readonly
  base_url: https://5.nl19.seedit4.me
  verify_tls: true
  auth:
    type: sabnzbd_api_key
    api_key_env: SABNZBD_API_KEY
  endpoints:
    queue: /sabnzbd/api
  paths:
    remote_root: /home/seedit4me/sabnzbd/complete/
opnsense:
  enabled: true
  adapter: opnsense_readonly
  base_url: https://192.168.10.1
  verify_tls: false
  auth:
    type: basic_auth
    username_env: OPNSENSE_API_KEY
    password_env: OPNSENSE_API_SECRET
  endpoints:
    interfaces: /api/interfaces
    firewall_filter: /api/firewall/filter
    firewall_nat: /api/firewall/nat
    firewall_alias: /api/firewall/alias
    core_service: /api/core/service
    core_system: /api/core/system
    diagnostics: /api/diagnostics
    unbound_settings: /api/unbound/settings
    dhcp_leases: /api/dhcpv4/leases
EOF

echo "[3/4] Writing config/policy.yaml..."
cat > $CONTROL_PLANE_HOME/config/policy.yaml <<'EOF'
mode: read_only
phase: phase_1
logging:
  level: info
  json: true
  redact_secrets: true
  save_artifacts: true
  save_http_summaries: true
http:
  connect_timeout_seconds: 5
  read_timeout_seconds: 20
  retries: 2
  backoff_seconds: 1
  user_agent: control-plane/0.1
security:
  allow_state_changes: false
  allow_deletes: false
  allow_restarts: false
  require_explicit_write_enable: true
services:
  qnap_201:
    allow_browser_automation: true
    allow_api_reads: true
  sonarr:
    allow_api_reads: true
  radarr:
    allow_api_reads: true
  sportarr:
    allow_api_reads: true
  prowlarr:
    allow_api_reads: true
  plex:
    allow_api_reads: true
  seedbox_rtorrent:
    allow_api_reads: true
  seedbox_sabnzbd:
    allow_api_reads: true
  opnsense:
    allow_api_reads: true
    allow_insecure_tls: true
workflows:
  full_stack_health:
    enabled: true
  media_pipeline_inventory:
    enabled: true
  sports_path_validation:
    enabled: true
  downloader_audit:
    enabled: true
  firewall_health:
    enabled: true
EOF

echo "[4/4] Writing secrets/.env ..."
chmod 700 $CONTROL_PLANE_HOME/secrets
cat > $CONTROL_PLANE_HOME/secrets/.env <<'EOF'
# =============================================================
# control-plane secrets
# chmod 600 this file — never commit to git
# =============================================================

# ── QNAP 201 (192.168.10.201) ─────────────────────────────────
QNAP201_USERNAME=admin
QNAP201_PASSWORD=

# ── Sonarr  →  http://192.168.10.201:8989/settings/general ───
SONARR_API_KEY=2731353744504eb0a5d4225b7c40dfc6

# ── Radarr  →  http://192.168.10.201:7878/settings/general ───
RADARR_API_KEY=2a3636f0d3b44ee48082c96298dc5194

# ── Sportarr  →  http://192.168.10.201:1867/settings/general ─
SPORTARR_API_KEY=

# ── Prowlarr (confirmed live 2026-04-01) ─────────────────────
PROWLARR_API_KEY=9dbcdf169ec8477bb051fdc60e30f17a

# ── Plex (confirmed live 2026-04-01) ─────────────────────────
PLEX_TOKEN=pH-SxG9ATTLapNrDe_dY

# ── Seedbox ruTorrent (confirmed live 2026-04-01) ────────────
SEEDBOX_USERNAME=seedit4me
SEEDBOX_PASSWORD=+Huckbear17

# ── Seedbox SABnzbd (confirmed live 2026-04-01) ──────────────
SABNZBD_API_KEY=4ff384f1326f49d58daf1df91a277db8

# ── OPNsense  →  System → Access → Users → API Keys ─────────
OPNSENSE_API_KEY=
OPNSENSE_API_SECRET=
EOF
chmod 600 $CONTROL_PLANE_HOME/secrets/.env

echo ""
echo "===== Done. Verify: ====="
find $CONTROL_PLANE_HOME -maxdepth 2 | sort
echo ""
echo "===== Permissions ====="
ls -ld $CONTROL_PLANE_HOME/secrets
ls -la $CONTROL_PLANE_HOME/secrets/
echo ""
echo "===== Still need manual entry in $CONTROL_PLANE_HOME/secrets/.env ====="
echo "  QNAP201_PASSWORD"
echo "  SONARR_API_KEY   → http://192.168.10.201:8989/settings/general"
echo "  RADARR_API_KEY   → http://192.168.10.201:7878/settings/general"
echo "  SPORTARR_API_KEY → http://192.168.10.201:1867/settings/general"
echo "  OPNSENSE_API_KEY + OPNSENSE_API_SECRET → OPNsense UI"
