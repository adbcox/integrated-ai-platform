# cleanuparr — Vault read access for arr API keys + rTorrent download
# client + Cleanuparr's own admin api_key (used by bootstrap script via
# rendered sidecar credentials.env).
#
# D-17-49 (2026-05-03) — §18.G component 3.
# D-17-76 commit-2 (2026-05-04) — extends with rtorrent + cleanuparr/api.
#
# SABnzbd is intentionally NOT included here. Cleanuparr's deployed
# image binary does not implement SABnzbd as a download-client type
# (verified 2026-05-04 via API probes + binary `strings` analysis);
# Cleanuparr never reads SABnzbd creds. SABnzbd remains platform-canonical
# at secret/seedbox/sabnzbd for non-Cleanuparr consumers (Sonarr/Radarr
# direct usage, future queue-monitor sidecars). See SMOKE.md "Known
# limitation — Cleanuparr SABnzbd coverage gap" for context.

path "secret/data/arr/sonarr" {
  capabilities = ["read"]
}

path "secret/data/arr/radarr" {
  capabilities = ["read"]
}

path "secret/data/seedbox/rtorrent" {
  capabilities = ["read"]
}

path "secret/data/cleanuparr/api" {
  capabilities = ["read"]
}
