exit_after_auth = true

vault {
  address = "http://vault-server:8200"
}

auto_auth {
  method "approle" {
    config = {
      role_id_file_path   = "/vault/approle/role_id"
      secret_id_file_path = "/vault/approle/secret_id"
      remove_secret_id_file_after_reading = false
    }
  }

  sink "file" {
    config = {
      path = "/vault/secrets/.token"
    }
  }
}

template {
  source      = "/vault/agent-config/credentials.env.tmpl"
  destination = "/vault/secrets/credentials.env"
}
