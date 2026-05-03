# scraparr — read-only access to arr-stack API keys for metrics export
# D-17-46 §18.G component 1

path "secret/data/arr/sonarr" {
  capabilities = ["read"]
}

path "secret/data/arr/radarr" {
  capabilities = ["read"]
}

path "secret/data/arr/prowlarr" {
  capabilities = ["read"]
}
