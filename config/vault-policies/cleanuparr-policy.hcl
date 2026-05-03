# cleanuparr — read access to arr API keys for queue remediation/search retries.
# D-17-49 (2026-05-03) — §18.G component 3.

path "secret/data/arr/sonarr" {
  capabilities = ["read"]
}

path "secret/data/arr/radarr" {
  capabilities = ["read"]
}
