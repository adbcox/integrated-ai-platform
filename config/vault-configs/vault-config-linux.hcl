# Vault config — Linux (Threadripper, future deployment)
# IPC_LOCK is available; disable_mlock should be false in production.
# Compose must include: cap_add: [IPC_LOCK]

storage "file" {
  path = "/vault/data"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = true
  telemetry {
    unauthenticated_metrics_access = true
  }
}

# Auto-unseal via Transit (seal-vault container)
seal "transit" {
  address         = "http://seal-vault:8201"
  disable_renewal = "false"
  key_name        = "autounseal"
  mount_path      = "transit/"
  token_file      = "/vault/config/autounseal-token"
}

api_addr     = "http://${VAULT_API_HOST}:8200"   # set via env at deploy time
cluster_addr = "http://0.0.0.0:8201"
ui           = true

# Linux — mlock available; keep enabled for production
disable_mlock = false

# Prometheus telemetry (Block 2 readiness)
telemetry {
  prometheus_retention_time      = "30s"
  disable_hostname               = true
  unauthenticated_metrics_access = true
}
