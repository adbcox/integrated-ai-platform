# bazarr — read access to Sonarr + Radarr API keys for Bazarr integration.
# D-17-47 (2026-05-03) — §18.G component 5 (Bazarr subtitle automation).

path "secret/data/arr/sonarr" {
  capabilities = ["read"]
}

path "secret/data/arr/radarr" {
  capabilities = ["read"]
}
