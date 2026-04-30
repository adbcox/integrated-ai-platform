workspace "Integrated AI Platform" "Phase 13/14 baseline — 2026-04-30" {

    model {
        operator = person "Operator" "Platform maintainer"

        platform = softwareSystem "AI Platform" "Mac Mini M5 control plane" {
            caddy       = container "Caddy"          "Reverse proxy + TLS (*.internal)"    "Caddy 2.x"
            vault       = container "Vault"           "Secret store + AppRole auth"          "HashiCorp Vault"
            netbox      = container "NetBox"          "CMDB — service + network inventory"   "NetBox CE"
            plane       = container "Plane"           "Roadmap + issue tracker"              "Plane CE"
            inventree   = container "InvenTree"       "Parts CMDB"                           "InvenTree"
            grafana     = container "Grafana"         "Observability dashboards"             "Grafana OSS"
            victoriametrics = container "VictoriaMetrics" "Metrics store"                   "VictoriaMetrics"
            zabbix      = container "Zabbix"          "Host + service monitoring"            "Zabbix 7.4"
            loki        = container "Loki"            "Log aggregation (Caddy per-site)"     "Grafana Loki"
            structurizr = container "Structurizr"     "C4 architecture diagrams"             "Structurizr Lite"
            mkdocs      = container "MkDocs"          "Internal documentation site"          "MkDocs Material"
            ollama      = container "Ollama"          "Local LLM inference"                  "Ollama"
            litellm     = container "LiteLLM"         "LLM gateway (local models)"           "LiteLLM"
            openhands   = container "OpenHands"       "AI coding agent"                      "OpenHands"
            obot        = container "Obot"            "AI automation agent"                  "Obot"
            plex        = container "Plex"            "Media server"                         "Plex Media Server"
        }

        operator -> caddy "accesses via *.internal"
        caddy -> vault
        caddy -> netbox
        caddy -> plane
        caddy -> inventree
        caddy -> grafana
        caddy -> zabbix
        caddy -> structurizr
        caddy -> mkdocs
        caddy -> openhands
        caddy -> obot
        caddy -> plex
        vault -> caddy "TLS certs via ACME"
        litellm -> ollama
        openhands -> litellm
        obot -> litellm
        grafana -> victoriametrics
        grafana -> loki
    }

    views {
        systemContext platform "SystemContext" {
            include *
            autolayout lr
        }
        container platform "Containers" {
            include *
            autolayout lr
        }
        theme default
    }
}
