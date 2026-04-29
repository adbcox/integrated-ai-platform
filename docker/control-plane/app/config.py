from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    # Auth
    operator_argon2_hash: str = ""
    tier3_window_seconds: int = 300

    # Tailnet
    tailnet_cidr: str = "100.64.0.0/10"
    require_tailnet: bool = True

    # Service port (host-exposed and bound by uvicorn)
    listen_port: int = 8086

    # Vault
    vault_addr: str = "http://vault-server:8200"
    vault_token_path: str = "/vault/secrets/.vault-token"

    # Docker socket proxy
    docker_host: str = "tcp://docker-socket-proxy-control:2375"

    # Service API keys (rendered by vault-agent into credentials.env)
    sonarr_api_key: str = ""
    radarr_api_key: str = ""
    prowlarr_api_key: str = ""

    # Restic / MinIO (for snapshot listing)
    restic_repository: str = ""
    restic_password: str = ""
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    # File-system paths
    audit_log_path: str = "/vault/logs/audit.log"
    caddy_access_log_path: str = "/var/log/caddy/access.log"
    trigger_dir: str = "/var/run/iap"
    service_registry_path: str = "/app/service-registry.yaml"
    actions_log_path: str = "/var/log/control-plane/actions.jsonl"

    # CMDB source: yaml (registry file) | netbox (in-cluster NetBox).
    # Block 4.C C5.2c — staged toggle. Default stays yaml during the
    # transition window; flip to netbox after C6 closes.
    cmdb_source: str = "yaml"

    # Service endpoints (host-side; control-plane reaches via host.docker.internal proxy)
    sonarr_url: str = "http://host.docker.internal:8989"
    radarr_url: str = "http://host.docker.internal:7878"
    prowlarr_url: str = "http://host.docker.internal:9696"
    topology_api_url: str = "http://host.docker.internal:8300"


settings = Settings()
