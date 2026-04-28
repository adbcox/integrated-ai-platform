# Vault config — Mac Mini (Colima/Docker Desktop)
# Critical: disable_mlock=true required because IPC_LOCK isn't available on Colima/macOS
# (Apple Silicon containers can't grant CAP_SETFCAP at runtime, blocking mlock).

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

api_addr     = "http://192.168.10.145:8200"
cluster_addr = "http://0.0.0.0:8201"
ui           = true

# macOS/Colima — mlock not available; use disable_mlock + named-volume audit logs
disable_mlock = true

# Prometheus telemetry (Block 2 readiness)
telemetry {
  prometheus_retention_time      = "30s"
  disable_hostname               = true
  unauthenticated_metrics_access = true
}
