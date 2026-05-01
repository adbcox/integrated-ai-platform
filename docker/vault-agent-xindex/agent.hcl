# Vault Agent — xindex (D-16-02.1)
#
# Runs once at compose-up, authenticates the xindex AppRole, renders
# the NetBox API credentials env file, then exits. The xindex service
# depends on this sidecar with `service_completed_successfully` so it
# only starts after credentials are on disk.
#
# Scope is intentionally narrow: only NetBox in this deliverable.
# Future external sources (Plane in D-16-02.2) extend this config
# with additional templates — never with a broader policy.

vault {
  address = "http://vault-server:8200"
}

auto_auth {
  method "approle" {
    config = {
      role_id_file_path                   = "/vault/approle/role-id"
      secret_id_file_path                 = "/vault/approle/secret-id"
      remove_secret_id_file_after_reading = false
    }
  }

  sink "file" {
    config = {
      path = "/vault/secrets/.vault-token"
    }
  }
}

template {
  source      = "/vault/agent-config/netbox-credentials.env.tmpl"
  destination = "/vault/secrets/netbox-credentials.env"
  perms       = "0444"
}

template {
  source      = "/vault/agent-config/plane-credentials.env.tmpl"
  destination = "/vault/secrets/plane-credentials.env"
  perms       = "0444"
}

exit_after_auth = true
