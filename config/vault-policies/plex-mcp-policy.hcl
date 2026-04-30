# plex-mcp — read-only access to Plex and arr credentials
# Updated Phase 14 D-DOC (2026-04-29) — Phase G migration to Vault Agent sidecar

path "secret/data/plex/api" {
  capabilities = ["read"]
}

path "secret/data/arr/sonarr" {
  capabilities = ["read"]
}

path "secret/data/arr/radarr" {
  capabilities = ["read"]
}
