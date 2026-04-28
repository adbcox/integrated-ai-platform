pid_file = "/tmp/agent.pid"

vault {
  address = "http://vault-server:8200"
}

auto_auth {
  method "approle" {
    mount_path = "auth/approle"
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
  source      = "/vault/agent-config/credentials.env.tmpl"
  destination = "/vault/secrets/credentials.env"
  perms       = "0444"
}

exit_after_auth = true
