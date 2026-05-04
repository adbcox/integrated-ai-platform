# lidarr — read access for Lidarr-side integration bootstrap.
# D-17-87 §18.G component: Lidarr deployment.

path "secret/data/arr/prowlarr" {
  capabilities = ["read"]
}

path "secret/data/arr/lidarr" {
  capabilities = ["read"]
}
