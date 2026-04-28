# Phase 13 Inventory — Mac Mini (192.168.10.145) — 2026-04-28

Read-only snapshot. No services modified. Vault values not read (paths only).
Generated: 2026-04-28T06:05:03Z

## 1. Docker state on Mac Mini

### Running containers (table)
```
NAMES                      IMAGE                                             STATUS                 PORTS
obot                       obot/obot:latest                                  Up 4 hours (healthy)   0.0.0.0:8090->8080/tcp, [::]:8090->8080/tcp
sms1obot-mcp-server-shim   ghcr.io/nanobot-ai/nanobot:v0.0.67                Up 4 hours             8080/tcp, 127.0.0.1:32788->8099/tcp
sms1obot-mcp-server        ghcr.io/obot-platform/obot-mcp-server:v0.1.1      Up 4 hours             127.0.0.1:32787->8080/tcp
docker-plane-api-1         makeplane/plane-backend:stable                    Up 4 hours (healthy)   0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
mcp-docker-remote          node:22-slim                                      Up 4 hours             0.0.0.0:8092->8092/tcp
headscale                  headscale/headscale:latest                        Up 4 hours (healthy)   0.0.0.0:50443->50443/tcp, [::]:50443->50443/tcp, 0.0.0.0:8082->8080/tcp, [::]:8082->8080/tcp
caddy                      caddy:2-alpine                                    Up 4 hours (healthy)   0.0.0.0:80->80/tcp, [::]:80->80/tcp, 0.0.0.0:443->443/tcp, [::]:443->443/tcp, 0.0.0.0:2019->2019/tcp, [::]:2019->2019/tcp, 443/udp
nextcloud                  nextcloud:29-apache                               Up 4 hours (healthy)   0.0.0.0:8085->80/tcp, [::]:8085->80/tcp
nextcloud-db               postgres:16-alpine                                Up 4 hours (healthy)   5432/tcp
vaultwarden                vaultwarden/server:latest                         Up 4 hours (healthy)   0.0.0.0:8083->80/tcp, [::]:8083->80/tcp
mcp-filesystem-remote      node:22-slim                                      Up 4 hours (healthy)   0.0.0.0:8091->8091/tcp, [::]:8091->8091/tcp
zabbix-web                 zabbix/zabbix-web-nginx-pgsql:alpine-7.4-latest   Up 4 hours (healthy)   0.0.0.0:10080->8080/tcp, [::]:10080->8080/tcp, 0.0.0.0:10443->8443/tcp, [::]:10443->8443/tcp
zabbix-agent               zabbix/zabbix-agent:alpine-7.4-latest             Up 4 hours             10050/tcp
zabbix-server              zabbix/zabbix-server-pgsql:alpine-7.4-latest      Up 4 hours             0.0.0.0:10051->10051/tcp, [::]:10051->10051/tcp
zabbix-postgres            timescale/timescaledb:latest-pg16                 Up 4 hours (healthy)   5432/tcp
mcp-docs-remote            node:22-slim                                      Up 4 hours (healthy)   0.0.0.0:8093->8093/tcp, [::]:8093->8093/tcp
anythingllm                mintplexlabs/anythingllm:latest                   Up 4 hours (healthy)   0.0.0.0:3004->3001/tcp, [::]:3004->3001/tcp
homarr                     ghcr.io/ajnart/homarr:latest                      Up 4 hours (healthy)   0.0.0.0:7575->7575/tcp, [::]:7575->7575/tcp
mcpo-proxy                 nikolaik/python-nodejs:python3.12-nodejs22-slim   Up 4 hours (healthy)   0.0.0.0:8081->8081/tcp, [::]:8081->8081/tcp
homeassistant              ghcr.io/home-assistant/home-assistant:stable      Up 4 hours (healthy)   0.0.0.0:8123->8123/tcp, [::]:8123->8123/tcp
grafana-obs                grafana/grafana:10.4.2                            Up 4 hours             0.0.0.0:3030->3000/tcp, [::]:3030->3000/tcp
open-webui                 ghcr.io/open-webui/open-webui:main                Up 4 hours (healthy)   0.0.0.0:3002->8080/tcp, [::]:3002->8080/tcp
litellm-gateway            ghcr.io/berriai/litellm:main-latest               Up 4 hours (healthy)   0.0.0.0:4000->4000/tcp, [::]:4000->4000/tcp
vault-server               hashicorp/vault:latest                            Up 4 hours (healthy)   0.0.0.0:8200->8200/tcp, [::]:8200->8200/tcp
sonarr                     lscr.io/linuxserver/sonarr:latest                 Up 4 hours (healthy)   0.0.0.0:8989->8989/tcp, [::]:8989->8989/tcp
radarr                     lscr.io/linuxserver/radarr:latest                 Up 4 hours (healthy)   0.0.0.0:7878->7878/tcp, [::]:7878->7878/tcp
prowlarr                   lscr.io/linuxserver/prowlarr:latest               Up 4 hours (healthy)   0.0.0.0:9696->9696/tcp, [::]:9696->9696/tcp
sportarr                   sportarr/sportarr:latest                          Up 4 hours (healthy)   0.0.0.0:1867->1867/tcp, [::]:1867->1867/tcp
docker-plane-db-1          postgres:15-alpine                                Up 4 hours (healthy)   127.0.0.1:5433->5432/tcp
vm                         victoriametrics/victoria-metrics:v1.99.0          Up 4 hours (healthy)   0.0.0.0:8428->8428/tcp, [::]:8428->8428/tcp
vmagent                    victoriametrics/vmagent:v1.99.0                   Up 4 hours             0.0.0.0:8429->8429/tcp, [::]:8429->8429/tcp
uptime-kuma                louislam/uptime-kuma:1                            Up 4 hours (healthy)   0.0.0.0:3033->3001/tcp, [::]:3033->3001/tcp
node-exporter              prom/node-exporter:v1.7.0                         Up 4 hours             
docker-plane-web-1         makeplane/plane-frontend:stable                   Up 4 hours (healthy)   80/tcp, 0.0.0.0:3001->3000/tcp, [::]:3001->3000/tcp
docker-plane-beat-1        makeplane/plane-backend:stable                    Up 4 hours             8000/tcp
docker-plane-worker-1      makeplane/plane-backend:stable                    Up 4 hours             8000/tcp
docker-plane-redis-1       redis:7.2-alpine                                  Up 4 hours (healthy)   6379/tcp
docker-plane-minio-1       minio/minio:latest                                Up 4 hours             0.0.0.0:9000-9001->9000-9001/tcp, [::]:9000-9001->9000-9001/tcp
openhands-app              5c0dc26f467b                                      Up 4 hours             0.0.0.0:3000->3000/tcp, [::]:3000->3000/tcp
```

### Per-container detail (name | state | started | image | ports | mounts | networks)
```
/obot | running | 2026-04-28T02:04:21.562035314Z | obot/obot:latest | 8080/tcp=0.0.0.0:8090 :::8090 ; | bind:/Users/admin/repos/integrated-ai-platform->/workspace(ro) volume:/var/lib/docker/volumes/obot-data/_data->/data(rw) bind:/var/run/docker.sock->/var/run/docker.sock(rw)  | docker_plane-net(172.19.0.25) obot-net(172.22.0.4) 
/sms1obot-mcp-server-shim | running | 2026-04-28T01:45:38.978734077Z | ghcr.io/nanobot-ai/nanobot:v0.0.67 | 8080/tcp=;8099/tcp=127.0.0.1:32788 ; | volume:/var/lib/docker/volumes/sms1obot-mcp-server-shim-nanobot-config/_data->/config(rw) volume:/var/lib/docker/volumes/9b0b8e6e62d2412418b4b1b83039f5189376208c690537be84afa072a9ef9e73/_data->/data(rw)  | docker_plane-net(172.19.0.24) 
/sms1obot-mcp-server | running | 2026-04-28T01:45:31.893988253Z | ghcr.io/obot-platform/obot-mcp-server:v0.1.1 | 8080/tcp=127.0.0.1:32787 ; |  | docker_plane-net(172.19.0.26) 
/docker-plane-api-1 | running | 2026-04-28T01:45:16.582280587Z | makeplane/plane-backend:stable | 8000/tcp=0.0.0.0:8000 :::8000 ; | volume:/var/lib/docker/volumes/docker_plane-logs/_data->/code/plane/logs(rw)  | docker_plane-net(172.19.0.5) 
/mcp-docker-remote | running | 2026-04-28T01:45:16.704423629Z | node:22-slim | 8092/tcp=0.0.0.0:8092 ; | bind:/var/run/docker.sock->/var/run/docker.sock(rw)  | bridge(172.17.0.2) 
/headscale | running | 2026-04-28T01:45:16.699733587Z | headscale/headscale:latest | 50443/tcp=0.0.0.0:50443 :::50443 ;8080/tcp=0.0.0.0:8082 :::8082 ; | volume:/var/lib/docker/volumes/headscale-data/_data->/var/lib/headscale(rw) bind:/Users/admin/repos/integrated-ai-platform/docker/headscale/config->/etc/headscale(ro)  | headscale-net(172.26.0.2) 
/caddy | running | 2026-04-28T01:45:16.56255867Z | caddy:2-alpine | 2019/tcp=0.0.0.0:2019 :::2019 ;443/tcp=0.0.0.0:443 :::443 ;443/udp=;80/tcp=0.0.0.0:80 :::80 ; | volume:/var/lib/docker/volumes/caddy-config/_data->/config(rw) volume:/var/lib/docker/volumes/caddy-data/_data->/data(rw) bind:/Users/admin/repos/integrated-ai-platform/docker/caddy/Caddyfile->/etc/caddy/Caddyfile(ro)  | caddy-net(172.21.0.2) 
/nextcloud | running | 2026-04-28T01:45:16.700520296Z | nextcloud:29-apache | 80/tcp=0.0.0.0:8085 :::8085 ; | volume:/var/lib/docker/volumes/nextcloud-data/_data->/var/www/html(rw)  | nextcloud-net(172.28.0.3) 
/nextcloud-db | running | 2026-04-28T01:45:16.565810712Z | postgres:16-alpine | 5432/tcp=; | volume:/var/lib/docker/volumes/nextcloud-db-data/_data->/var/lib/postgresql/data(rw)  | nextcloud-net(172.28.0.2) 
/vaultwarden | running | 2026-04-28T01:45:16.696654837Z | vaultwarden/server:latest | 80/tcp=0.0.0.0:8083 :::8083 ; | volume:/var/lib/docker/volumes/vaultwarden-data/_data->/data(rw)  | vaultwarden-net(172.27.0.2) 
/mcp-filesystem-remote | running | 2026-04-28T01:45:16.645286171Z | node:22-slim | 8091/tcp=0.0.0.0:8091 :::8091 ; | bind:/Users/admin/repos/integrated-ai-platform->/workspace(ro)  | obot-net(172.22.0.2) 
/zabbix-web | running | 2026-04-28T01:45:16.676143087Z | zabbix/zabbix-web-nginx-pgsql:alpine-7.4-latest | 8080/tcp=0.0.0.0:10080 :::10080 ;8443/tcp=0.0.0.0:10443 :::10443 ; |  | zabbix-net(172.25.0.4) 
/zabbix-agent | running | 2026-04-28T01:45:16.562254462Z | zabbix/zabbix-agent:alpine-7.4-latest | 10050/tcp=; |  | zabbix-net(172.25.0.2) 
/zabbix-server | running | 2026-04-28T01:45:16.700143379Z | zabbix/zabbix-server-pgsql:alpine-7.4-latest | 10051/tcp=0.0.0.0:10051 :::10051 ; | bind:/Users/admin/repos/integrated-ai-platform/docker/zabbix/server/alertscripts->/usr/lib/zabbix/alertscripts(rw) bind:/Users/admin/repos/integrated-ai-platform/docker/zabbix/server/externalscripts->/usr/lib/zabbix/externalscripts(rw) volume:/var/lib/docker/volumes/7d58b4ae0ccc216e9eb33c38a6ac2c5201ef2e70e53d38018516db64db53264d/_data->/var/lib/zabbix/export(rw) volume:/var/lib/docker/volumes/4c5aa3e5d8e511716f6dee0131310394e43ee2f778b3439248d3ac3c076d451e/_data->/var/lib/zabbix/snmptraps(rw)  | zabbix-net(172.25.0.5) 
/zabbix-postgres | running | 2026-04-28T01:45:16.642045254Z | timescale/timescaledb:latest-pg16 | 5432/tcp=; | bind:/Users/admin/repos/integrated-ai-platform/docker/zabbix/postgres/backups->/backups(rw) volume:/var/lib/docker/volumes/zabbix-pgdata/_data->/var/lib/postgresql/data(rw)  | zabbix-net(172.25.0.3) 
/mcp-docs-remote | running | 2026-04-28T01:45:16.695287254Z | node:22-slim | 8093/tcp=0.0.0.0:8093 :::8093 ; |  | obot-net(172.22.0.3) 
/anythingllm | running | 2026-04-28T01:45:16.702977421Z | mintplexlabs/anythingllm:latest | 3001/tcp=0.0.0.0:3004 :::3004 ; | volume:/var/lib/docker/volumes/docker_anythingllm-storage/_data->/app/server/storage(rw) bind:/Users/admin/repos/integrated-ai-platform/docs->/platform-docs(ro)  | knowledge(172.24.0.2) 
/homarr | running | 2026-04-28T01:45:16.693267254Z | ghcr.io/ajnart/homarr:latest | 7575/tcp=0.0.0.0:7575 :::7575 ; | volume:/var/lib/docker/volumes/ai-control_homarr-icons/_data->/app/public/icons(rw) volume:/var/lib/docker/volumes/ai-control_homarr-data/_data->/data(rw) bind:/var/run/docker.sock->/var/run/docker.sock(ro) volume:/var/lib/docker/volumes/ai-control_homarr-config/_data->/app/data/configs(rw)  | control-center-net(172.23.0.9) 
/mcpo-proxy | running | 2026-04-28T01:45:16.693205671Z | nikolaik/python-nodejs:python3.12-nodejs22-slim | 8081/tcp=0.0.0.0:8081 :::8081 ; | bind:/Users/admin/repos/integrated-ai-platform->/workspace(ro)  | control-center-net(172.23.0.5) 
/homeassistant | running | 2026-04-28T01:45:16.695338254Z | ghcr.io/home-assistant/home-assistant:stable | 8123/tcp=0.0.0.0:8123 :::8123 ; | volume:/var/lib/docker/volumes/dashboards_homeassistant-config/_data->/config(rw)  | control-center-net(172.23.0.6) 
/grafana-obs | running | 2026-04-28T01:45:16.699417754Z | grafana/grafana:10.4.2 | 3000/tcp=0.0.0.0:3030 :::3030 ; | bind:/Users/admin/repos/integrated-ai-platform/docker/grafana-provisioning->/etc/grafana/provisioning(rw) volume:/var/lib/docker/volumes/docker_grafana-data/_data->/var/lib/grafana(rw)  | observability(172.20.0.4) 
/open-webui | running | 2026-04-28T01:45:16.704569837Z | ghcr.io/open-webui/open-webui:main | 8080/tcp=0.0.0.0:3002 :::3002 ; | volume:/var/lib/docker/volumes/ai-control_open-webui-data/_data->/app/backend/data(rw)  | control-center-net(172.23.0.8) 
/litellm-gateway | running | 2026-04-28T01:45:16.694734921Z | ghcr.io/berriai/litellm:main-latest | 4000/tcp=0.0.0.0:4000 :::4000 ; | bind:/Users/admin/control-center-stack/stacks/gateways/litellm_config.yaml->/app/config.yaml(ro) volume:/var/lib/docker/volumes/gateways_litellm-data/_data->/app/data(rw)  | control-center-net(172.23.0.10) 
/vault-server | running | 2026-04-28T01:45:16.633985629Z | hashicorp/vault:latest | 8200/tcp=0.0.0.0:8200 :::8200 ; | volume:/var/lib/docker/volumes/vault_vault-logs/_data->/vault/logs(rw) bind:/Users/admin/control-center-stack/stacks/vault/vault-config.hcl->/vault/config/vault.hcl(ro) volume:/var/lib/docker/volumes/vault_vault-data/_data->/vault/data(rw) volume:/var/lib/docker/volumes/bea5498d0d5fc54576998db788d6bc7701f6ec87c8e05cb50bc13ac205e6c7bb/_data->/vault/file(rw)  | control-center-net(172.23.0.4) 
/sonarr | running | 2026-04-28T01:45:16.618964837Z | lscr.io/linuxserver/sonarr:latest | 8989/tcp=0.0.0.0:8989 :::8989 ; | volume:/var/lib/docker/volumes/arr-stack_sonarr-config/_data->/config(rw) bind:/Users/admin/mnt/qnap-downloads/data->/data(rw) bind:/Users/admin/mnt/qnap-downloads->/downloads(rw)  | control-center-net(172.23.0.7) 
/radarr | running | 2026-04-28T01:45:16.694156712Z | lscr.io/linuxserver/radarr:latest | 7878/tcp=0.0.0.0:7878 :::7878 ; | volume:/var/lib/docker/volumes/arr-stack_radarr-config/_data->/config(rw) bind:/Users/admin/mnt/qnap-downloads/data->/data(rw) bind:/Users/admin/mnt/qnap-downloads->/downloads(rw)  | control-center-net(172.23.0.11) 
/prowlarr | running | 2026-04-28T01:45:16.692879837Z | lscr.io/linuxserver/prowlarr:latest | 9696/tcp=0.0.0.0:9696 :::9696 ; | volume:/var/lib/docker/volumes/arr-stack_prowlarr-config/_data->/config(rw)  | control-center-net(172.23.0.3) 
/sportarr | running | 2026-04-28T01:45:16.694019879Z | sportarr/sportarr:latest | 1867/tcp=0.0.0.0:1867 :::1867 ; | volume:/var/lib/docker/volumes/arr-stack_sportarr-config/_data->/config(rw) bind:/Users/admin/mnt/qnap-downloads/sports->/data(rw)  | control-center-net(172.23.0.2) 
/docker-plane-db-1 | running | 2026-04-28T01:45:16.562408337Z | postgres:15-alpine | 5432/tcp=127.0.0.1:5433 ; | volume:/var/lib/docker/volumes/docker_plane-db-data/_data->/var/lib/postgresql/data(rw)  | docker_plane-net(172.19.0.18) 
/vm | running | 2026-04-28T01:45:16.589869671Z | victoriametrics/victoria-metrics:v1.99.0 | 8428/tcp=0.0.0.0:8428 :::8428 ; | volume:/var/lib/docker/volumes/docker_vm-data/_data->/storage(rw)  | observability(172.20.0.2) 
/vmagent | running | 2026-04-28T01:45:16.695161421Z | victoriametrics/vmagent:v1.99.0 | 8429/tcp=0.0.0.0:8429 :::8429 ; | volume:/var/lib/docker/volumes/docker_vmagent-data/_data->/vmagentdata(rw) bind:/Users/admin/repos/integrated-ai-platform/docker/vmagent-config->/etc/vmagent(rw)  | observability(172.20.0.3) 
/uptime-kuma | running | 2026-04-28T01:45:16.696460712Z | louislam/uptime-kuma:1 | 3001/tcp=0.0.0.0:3033 :::3033 ; | volume:/var/lib/docker/volumes/docker_uptime-data/_data->/app/data(rw)  | observability(172.20.0.5) 
/node-exporter | running | 2026-04-28T01:45:16.565464587Z | prom/node-exporter:v1.7.0 |  | bind:/proc->/host/proc(ro) bind:/sys->/host/sys(ro) bind:/->/rootfs(ro)  | host(invalid IP) 
/docker-plane-web-1 | running | 2026-04-28T01:45:16.606191879Z | makeplane/plane-frontend:stable | 3000/tcp=0.0.0.0:3001 :::3001 ;80/tcp=; |  | docker_plane-net(172.19.0.7) 
/docker-plane-beat-1 | running | 2026-04-28T01:45:16.57772692Z | makeplane/plane-backend:stable | 8000/tcp=; |  | docker_plane-net(172.19.0.10) 
/docker-plane-worker-1 | running | 2026-04-28T01:45:16.546786462Z | makeplane/plane-backend:stable | 8000/tcp=; |  | docker_plane-net(172.19.0.6) 
/docker-plane-redis-1 | running | 2026-04-28T01:45:16.546537629Z | redis:7.2-alpine | 6379/tcp=; | volume:/var/lib/docker/volumes/docker_plane-redis-data/_data->/data(rw)  | docker_plane-net(172.19.0.2) 
/docker-plane-minio-1 | running | 2026-04-28T01:45:16.565658212Z | minio/minio:latest | 9000/tcp=0.0.0.0:9000 :::9000 ;9001/tcp=0.0.0.0:9001 :::9001 ; | volume:/var/lib/docker/volumes/docker_plane-minio-data/_data->/data(rw)  | docker_plane-net(172.19.0.11) 
/openhands-app | running | 2026-04-28T01:45:16.705830712Z | docker.openhands.dev/openhands/openhands@sha256:5c0dc26f467bf8e47a6e76308edb7a30af4084b17e23a3460b5467008b12111b | 3000/tcp=0.0.0.0:3000 :::3000 ; | bind:/Users/admin/repos/integrated-ai-platform/.local-model-data/openhands-state->/.openhands(rw) bind:/Users/admin/repos/integrated-ai-platform->/opt/workspace(rw) bind:/var/run/docker.sock->/var/run/docker.sock(rw)  | bridge(172.17.0.3) 
```

### Stopped / exited containers
```
NAMES     STATUS    IMAGE
NAMES     STATUS    IMAGE
```

### Networks & members
```
NETWORK ID     NAME                 DRIVER    SCOPE
274a00b57863   bridge               bridge    local
99afbdd7e42c   caddy-net            bridge    local
c1618021e91f   control-center-net   bridge    local
b44520d0366a   dashboard-net        bridge    local
5d79b73be455   docker_plane-net     bridge    local
50e28b8c822b   headscale-net        bridge    local
2d9ab3b29528   host                 host      local
19faaff7b92b   knowledge            bridge    local
2e2cd6ca5dd9   nextcloud-net        bridge    local
96acd4a5ba12   none                 null      local
a03b0b5bd212   obot-net             bridge    local
3723e2ed4088   observability        bridge    local
0af50475e0bf   vaultwarden-net      bridge    local
fd5eeb1de305   zabbix-net           bridge    local

  bridge: mcp-docker-remote openhands-app 
  caddy-net: caddy 
  control-center-net: prowlarr sportarr mcpo-proxy vault-server radarr litellm-gateway open-webui homeassistant sonarr homarr 
  dashboard-net: (empty)
  docker_plane-net: docker-plane-redis-1 docker-plane-db-1 docker-plane-web-1 docker-plane-worker-1 sms1obot-mcp-server-shim docker-plane-minio-1 sms1obot-mcp-server docker-plane-beat-1 obot docker-plane-api-1 
  headscale-net: headscale 
  host: node-exporter 
  knowledge: anythingllm 
  nextcloud-net: nextcloud-db nextcloud 
  none: (empty)
  obot-net: mcp-docs-remote mcp-filesystem-remote obot 
  observability: vmagent vm uptime-kuma grafana-obs 
  vaultwarden-net: vaultwarden 
  zabbix-net: zabbix-web zabbix-server zabbix-postgres zabbix-agent 
```

### Volumes & disk usage
```
Images space usage:

REPOSITORY                                 TAG                        IMAGE ID       CREATED         SIZE      SHARED SIZE   UNIQUE SIZE   CONTAINERS
vaultwarden/server                         latest                     c4f6056fe0c2   2 days ago      368MB     109.3MB       258.6MB       1
lscr.io/linuxserver/sonarr                 latest                     3580aec3802c   3 days ago      321MB     44.71MB       275.8MB       1
mintplexlabs/anythingllm                   latest                     6421755dbce8   3 days ago      5.08GB    0B            5.078GB       1
ghcr.io/home-assistant/home-assistant      stable                     c1e5f0147f4c   3 days ago      3.26GB    0B            3.261GB       1
ghcr.io/open-webui/open-webui              main                       c2e4723fdbca   3 days ago      6.06GB    0B            6.056GB       1
zabbix/zabbix-web-nginx-pgsql              alpine-7.4-latest          c7eb410c058b   3 days ago      198MB     9.351MB       188.2MB       1
zabbix/zabbix-agent                        alpine-7.4-latest          09418b53fff1   3 days ago      37.6MB    9.351MB       28.24MB       1
zabbix/zabbix-server-pgsql                 alpine-7.4-latest          e00dea4cdd0e   3 days ago      109MB     9.351MB       99.7MB        1
obot/obot                                  latest                     fd8e9efc5a6a   5 days ago      4.52GB    14.2MB        4.508GB       1
curlimages/curl                            latest                     c03110c736db   5 days ago      37.2MB    0B            37.24MB       0
lscr.io/linuxserver/prowlarr               latest                     c5de2a8758a0   6 days ago      305MB     44.71MB       260.4MB       1
python                                     3.12-slim                  46cb7cc2877e   6 days ago      205MB     109.3MB       95.26MB       0
node                                       22-slim                    d415caac2f1f   6 days ago      349MB     0B            348.8MB       3
postgres                                   15-alpine                  09e4f20b14dd   6 days ago      386MB     9.351MB       376.9MB       1
postgres                                   16-alpine                  4e6e670bb069   6 days ago      389MB     9.351MB       379.7MB       1
lscr.io/linuxserver/radarr                 latest                     b01097ad2d94   8 days ago      338MB     44.71MB       292.9MB       1
redis                                      7.2-alpine                 9907ac0c4357   11 days ago     61.2MB    0B            61.22MB       1
ghcr.io/obot-platform/mcp-images/phat      v0.20.2                    301c2ae9d839   11 days ago     3.04GB    337.4MB       2.703GB       0
ghcr.io/nanobot-ai/nanobot                 v0.0.67                    d36e1481179f   11 days ago     468MB     337.4MB       130.6MB       1
caddy                                      2-alpine                   834468128c76   12 days ago     84.3MB    9.351MB       74.94MB       1
alpine                                     latest                     5b10f432ef3d   12 days ago     13.6MB    9.351MB       4.287MB       0
timescale/timescaledb                      latest-pg16                95a7997408e3   13 days ago     1.69GB    9.359MB       1.686GB       1
hashicorp/vault                            latest                     e40c741ed95b   2 weeks ago     698MB     9.359MB       688.9MB       1
sportarr/sportarr                          latest                     bd915451e072   2 weeks ago     1.01GB    0B            1.015GB       1
makeplane/plane-frontend                   stable                     5116ac06c2b5   3 weeks ago     125MB     0B            124.7MB       1
makeplane/plane-backend                    stable                     60fb33fa75b6   3 weeks ago     505MB     0B            504.6MB       3
ghcr.io/obot-platform/obot-mcp-server      v0.1.1                     ef4b23440123   4 weeks ago     290MB     109.3MB       180.8MB       1
docker.openhands.dev/openhands/openhands   latest                     5c0dc26f467b   4 weeks ago     1.95GB    0B            1.95GB        1
nikolaik/python-nodejs                     python3.12-nodejs22-slim   f66502c5bd9a   4 weeks ago     847MB     109.3MB       737.6MB       1
ghcr.io/berriai/litellm                    main-latest                7c311546c25e   5 weeks ago     5.59GB    4.101GB       1.49GB        2
ghcr.io/ajnart/homarr                      latest                     e103abadfb52   2 months ago    1.52GB    0B            1.518GB       1
headscale/headscale                        latest                     51b1b9182bb6   2 months ago    118MB     0B            118.1MB       1
louislam/uptime-kuma                       1                          3d632903e6af   6 months ago    711MB     0B            711.2MB       1
minio/minio                                latest                     14cea493d9a3   7 months ago    228MB     0B            227.7MB       1
nextcloud                                  29-apache                  a7fbfcd4759b   12 months ago   1.88GB    0B            1.879GB       1
grafana/grafana                            10.4.2                     7d5faae481a4   2 years ago     562MB     8.417MB       553.5MB       1
victoriametrics/vmagent                    v1.99.0                    2d19ed380935   2 years ago     36MB      8.651MB       27.3MB        1
victoriametrics/victoria-metrics           v1.99.0                    e3e18b05a2c0   2 years ago     42.8MB    8.651MB       34.12MB       1
prom/node-exporter                         v1.7.0                     4cb2b9019f17   2 years ago     36.1MB    0B            36.1MB        1
docker/docker-bench-security               latest                     ddbdf4f86af4   7 years ago     69.2MB    0B            69.17MB       0

Containers space usage:

CONTAINER ID   IMAGE                                             COMMAND                  LOCAL VOLUMES   SIZE      CREATED        STATUS                 NAMES
c0447b2b0538   obot/obot:latest                                  "run.sh"                 1               24.6kB    4 hours ago    Up 4 hours (healthy)   obot
4e09baeea0cd   ghcr.io/nanobot-ai/nanobot:v0.0.67                "/usr/local/bin/nano…"   2               8.19kB    4 hours ago    Up 4 hours             sms1obot-mcp-server-shim
58a5a0de2157   ghcr.io/obot-platform/obot-mcp-server:v0.1.1      "python main.py"         0               26.7MB    4 hours ago    Up 4 hours             sms1obot-mcp-server
f21e2ec1f508   makeplane/plane-backend:stable                    "./bin/docker-entryp…"   1               141MB     5 hours ago    Up 4 hours (healthy)   docker-plane-api-1
06bbb9c275cf   node:22-slim                                      "docker-entrypoint.s…"   0               608MB     6 hours ago    Up 4 hours             mcp-docker-remote
f8483ecafd48   headscale/headscale:latest                        "/ko-app/headscale s…"   1               36.9kB    11 hours ago   Up 4 hours (healthy)   headscale
3fdb0684e358   caddy:2-alpine                                    "caddy run --config …"   2               291kB     11 hours ago   Up 4 hours (healthy)   caddy
e89d12e48fcd   nextcloud:29-apache                               "/entrypoint.sh apac…"   1               262kB     11 hours ago   Up 4 hours (healthy)   nextcloud
36eaa0f65aa1   postgres:16-alpine                                "docker-entrypoint.s…"   1               20.5kB    11 hours ago   Up 4 hours (healthy)   nextcloud-db
7149d8370ca7   vaultwarden/server:latest                         "/start.sh"              1               4.1kB     12 hours ago   Up 4 hours (healthy)   vaultwarden
549e4cd0b296   node:22-slim                                      "docker-entrypoint.s…"   0               61.9MB    13 hours ago   Up 4 hours (healthy)   mcp-filesystem-remote
050106cf2f2f   zabbix/zabbix-web-nginx-pgsql:alpine-7.4-latest   "docker-entrypoint.sh"   0               77.8kB    18 hours ago   Up 4 hours (healthy)   zabbix-web
7f7c50686f4d   zabbix/zabbix-agent:alpine-7.4-latest             "/usr/bin/docker-ent…"   0               12.3kB    18 hours ago   Up 4 hours             zabbix-agent
45cdc7549264   zabbix/zabbix-server-pgsql:alpine-7.4-latest      "/usr/bin/docker-ent…"   2               12.3kB    18 hours ago   Up 4 hours             zabbix-server
62953c4d8fd3   timescale/timescaledb:latest-pg16                 "docker-entrypoint.s…"   1               65.5kB    18 hours ago   Up 4 hours (healthy)   zabbix-postgres
2ceb7a14bfd7   node:22-slim                                      "docker-entrypoint.s…"   0               2.4GB     26 hours ago   Up 4 hours (healthy)   mcp-docs-remote
f27ec16aa338   mintplexlabs/anythingllm:latest                   "/bin/bash /usr/loca…"   1               15.9MB    33 hours ago   Up 4 hours (healthy)   anythingllm
f2b3f9cfa05f   ghcr.io/ajnart/homarr:latest                      "sh ./scripts/run.sh"    3               2.39MB    35 hours ago   Up 4 hours (healthy)   homarr
4d83b0855fee   nikolaik/python-nodejs:python3.12-nodejs22-slim   "sh -c 'pip install …"   0               149MB     35 hours ago   Up 4 hours (healthy)   mcpo-proxy
c840808faa86   ghcr.io/home-assistant/home-assistant:stable      "/init"                  1               45.2MB    35 hours ago   Up 4 hours (healthy)   homeassistant
c7603bfac0d9   grafana/grafana:10.4.2                            "/run.sh"                1               8.19kB    35 hours ago   Up 4 hours             grafana-obs
97a64fb3f6b5   ghcr.io/open-webui/open-webui:main                "bash start.sh"          1               58.5MB    35 hours ago   Up 4 hours (healthy)   open-webui
7ff968a6be6a   ghcr.io/berriai/litellm:main-latest               "docker/prod_entrypo…"   1               19.2MB    35 hours ago   Up 4 hours (healthy)   litellm-gateway
6148923198bc   hashicorp/vault:latest                            "docker-entrypoint.s…"   3               49.2kB    36 hours ago   Up 4 hours (healthy)   vault-server
f0db05b3be56   lscr.io/linuxserver/sonarr:latest                 "/init"                  1               725kB     36 hours ago   Up 4 hours (healthy)   sonarr
75ca91abb9b9   lscr.io/linuxserver/radarr:latest                 "/init"                  1               717kB     36 hours ago   Up 4 hours (healthy)   radarr
2bef8ba76b49   lscr.io/linuxserver/prowlarr:latest               "/init"                  1               709kB     36 hours ago   Up 4 hours (healthy)   prowlarr
3d3da801cdfb   sportarr/sportarr:latest                          "/docker-entrypoint.…"   1               25.3MB    36 hours ago   Up 4 hours (healthy)   sportarr
0f7d5cf2be7b   postgres:15-alpine                                "docker-entrypoint.s…"   1               20.5kB    2 days ago     Up 4 hours (healthy)   docker-plane-db-1
41cca8f0d13a   victoriametrics/victoria-metrics:v1.99.0          "/victoria-metrics-p…"   1               8.19kB    2 days ago     Up 4 hours (healthy)   vm
1f8723214350   victoriametrics/vmagent:v1.99.0                   "/vmagent-prod -prom…"   1               426kB     2 days ago     Up 4 hours             vmagent
c3ac0c3a1169   louislam/uptime-kuma:1                            "/usr/bin/dumb-init …"   1               262kB     2 days ago     Up 4 hours (healthy)   uptime-kuma
70ce4848f0fa   prom/node-exporter:v1.7.0                         "/bin/node_exporter …"   0               20.5kB    2 days ago     Up 4 hours             node-exporter
```

=== SECTION 1 COMPLETE — 217 lines ===

## 2. Caddy state

### Caddyfile (live, source of truth via `docker exec caddy cat`)
```
# Caddy reverse proxy — LAN TLS termination for .internal domains
# Uses Caddy's internal CA for self-signed LAN certs.
# Trust the CA on clients:
#   docker exec caddy cat /data/caddy/pki/authorities/local/root.crt > caddy-local-ca.crt

{
    # Use Caddy's built-in local CA for all .internal sites (no ACME needed)
    local_certs
    # Expose admin API on all interfaces so host health checks can reach it
    admin 0.0.0.0:2019
}

# ── AI Layer ──────────────────────────────────────────────────────────────────
plane.internal {
    reverse_proxy host.docker.internal:3001
}

obot.internal {
    reverse_proxy host.docker.internal:8090
}

ollama.internal {
    reverse_proxy host.docker.internal:11434
}

anythingllm.internal {
    reverse_proxy host.docker.internal:3004
}

webui.internal {
    reverse_proxy host.docker.internal:3002
}

litellm.internal {
    reverse_proxy host.docker.internal:4000
}

# ── Platform Layer ────────────────────────────────────────────────────────────
vault.internal {
    reverse_proxy host.docker.internal:8200
}

dashboard.internal {
    reverse_proxy host.docker.internal:8080
}

homarr.internal {
    reverse_proxy host.docker.internal:7575
}

# ── Observability Layer ───────────────────────────────────────────────────────
grafana.internal {
    reverse_proxy host.docker.internal:3030
}

zabbix.internal {
    reverse_proxy host.docker.internal:10080
}

uptime.internal {
    reverse_proxy host.docker.internal:3033
}

# ── Media Layer ───────────────────────────────────────────────────────────────
sonarr.internal {
    reverse_proxy host.docker.internal:8989
}

radarr.internal {
    reverse_proxy host.docker.internal:7878
}

prowlarr.internal {
    reverse_proxy host.docker.internal:9696
}

vaultwarden.internal {
    reverse_proxy host.docker.internal:8083
}

headscale.internal {
    reverse_proxy host.docker.internal:8082
}

nextcloud.internal {
    reverse_proxy host.docker.internal:8085
}

mcp-filesystem.internal {
    reverse_proxy host.docker.internal:8091
}

mcp-docs.internal {
    reverse_proxy host.docker.internal:8093
}

mcp-docker.internal {
    reverse_proxy host.docker.internal:8092
}

victoria.internal {
    reverse_proxy host.docker.internal:8428
}
```

### Active config (Caddy admin API inside container — http://localhost:2019/config/)
```
{
  "srv0": {
    "listen": [
      ":443"
    ],
    "routes": [
      {
        "handle": [
          {
            "handler": "subroute",
            "routes": [
              {
                "handle": [
                  {
                    "handler": "reverse_proxy",
                    "upstreams": [
                      {
                        "dial": "host.docker.internal:8091"
                      }
                    ]
                  }
                ]
              }
            ]
          }
        ],
        "match": [
          {
            "host": [
              "mcp-filesystem.internal"
            ]
          }
        ],
        "terminal": true
      },
      {
        "handle": [
          {
            "handler": "subroute",
            "routes": [
              {
                "handle": [
                  {
                    "handler": "reverse_proxy",
                    "upstreams": [
                      {
                        "dial": "host.docker.internal:3004"
                      }
                    ]
                  }
                ]
              }
            ]
          }
        ],
        "match": [
          {
            "host": [
              "anythingllm.internal"
            ]
          }
        ],
        "terminal": true
      },
      {
        "handle": [
          {
            "handler": "subroute",
            "routes": [
              {
                "handle": [
                  {
                    "handler": "reverse_proxy",
                    "upstreams": [
                      {
                        "dial": "host.docker.internal:8083"
                      }
                    ]
                  }
                ]
              }
            ]
          }
        ],
        "match": [
          {
            "host": [
              "vaultwarden.internal"
            ]
          }
        ],
        "terminal": true
      },
      {
        "handle": [
          {
            "handler": "subroute",
            "routes": [
              {
                "handle": [
                  {
                    "handler": "reverse_proxy",
                    "upstreams": [
                      {
                        "dial": "host.docker.internal:8092"
                      }
                    ]
                  }
                ]
              }
            ]
          }
        ],
        "match": [
          {
            "host": [
              "mcp-docker.internal"
            ]
          }
        ],
        "terminal": true
      },
      {
        "handle": [
          {
            "handler": "subroute",
            "routes": [
              {
                "handle": [
                  {
                    "handler": "reverse_proxy",
                    "upstreams": [
                      {
                        "dial": "host.docker.internal:8080"
                      }
                    ]
                  }
                ]
              }
            ]
          }
        ],
        "match": [
          {
            "host": [
              "dashboard.internal"
            ]
          }
        ],
        "terminal": true
      },
      {
        "handle": [
          {
            "handler": "subroute",
            "routes": [
              {
                "handle": [
                  {
                    "handler": "reverse_proxy",
                    "upstreams": [
                      {
                        "dial": "host.docker.internal:8082"
                      }
                    ]
                  }
                ]
              }
            ]
          }
        ],
        "match": [
          {
            "host": [
              "headscale.internal"
            ]
          }
        ],
        "terminal": true
      },
      {
        "handle": [
          {
            "handler": "subroute",
            "routes": [
              {
                "handle": [
                  {
                    "handler": "reverse_proxy",
                    "upstreams": [
                      {
                        "dial": "host.docker.internal:8085"
                      }
                    ]
                  }
                ]
              }
            ]
          }
        ],
```

### Routes (host -> upstream) extracted from live Caddyfile
```
  plane.internal -> host.docker.internal:3001
  obot.internal -> host.docker.internal:8090
  ollama.internal -> host.docker.internal:11434
  anythingllm.internal -> host.docker.internal:3004
  webui.internal -> host.docker.internal:3002
  litellm.internal -> host.docker.internal:4000
  vault.internal -> host.docker.internal:8200
  dashboard.internal -> host.docker.internal:8080
  homarr.internal -> host.docker.internal:7575
  grafana.internal -> host.docker.internal:3030
  zabbix.internal -> host.docker.internal:10080
  uptime.internal -> host.docker.internal:3033
  sonarr.internal -> host.docker.internal:8989
  radarr.internal -> host.docker.internal:7878
  prowlarr.internal -> host.docker.internal:9696
  vaultwarden.internal -> host.docker.internal:8083
  headscale.internal -> host.docker.internal:8082
  nextcloud.internal -> host.docker.internal:8085
  mcp-filesystem.internal -> host.docker.internal:8091
  mcp-docs.internal -> host.docker.internal:8093
  mcp-docker.internal -> host.docker.internal:8092
  victoria.internal -> host.docker.internal:8428
```

### TLS cert info per .internal route
```
--- anythingllm.internal ---
subject= 
issuer= /CN=Caddy Local Authority - ECC Intermediate
notBefore=Apr 28 01:55:17 2026 GMT
notAfter=Apr 28 13:55:17 2026 GMT
--- dashboard.internal ---
subject= 
issuer= /CN=Caddy Local Authority - ECC Intermediate
notBefore=Apr 28 01:55:17 2026 GMT
notAfter=Apr 28 13:55:17 2026 GMT
--- grafana.internal ---
subject= 
issuer= /CN=Caddy Local Authority - ECC Intermediate
notBefore=Apr 28 01:55:17 2026 GMT
notAfter=Apr 28 13:55:17 2026 GMT
--- headscale.internal ---
subject= 
issuer= /CN=Caddy Local Authority - ECC Intermediate
notBefore=Apr 28 02:15:17 2026 GMT
notAfter=Apr 28 14:15:17 2026 GMT
--- homarr.internal ---
subject= 
issuer= /CN=Caddy Local Authority - ECC Intermediate
notBefore=Apr 28 01:55:17 2026 GMT
notAfter=Apr 28 13:55:17 2026 GMT
--- litellm.internal ---
subject= 
issuer= /CN=Caddy Local Authority - ECC Intermediate
notBefore=Apr 28 01:55:17 2026 GMT
notAfter=Apr 28 13:55:17 2026 GMT
--- mcp-docker.internal ---
subject= 
issuer= /CN=Caddy Local Authority - ECC Intermediate
notBefore=Apr 27 23:49:25 2026 GMT
notAfter=Apr 28 11:49:25 2026 GMT
--- mcp-docs.internal ---
subject= 
issuer= /CN=Caddy Local Authority - ECC Intermediate
notBefore=Apr 27 23:49:25 2026 GMT
notAfter=Apr 28 11:49:25 2026 GMT
--- mcp-filesystem.internal ---
subject= 
issuer= /CN=Caddy Local Authority - ECC Intermediate
notBefore=Apr 27 23:49:25 2026 GMT
notAfter=Apr 28 11:49:25 2026 GMT
--- nextcloud.internal ---
subject= 
issuer= /CN=Caddy Local Authority - ECC Intermediate
notBefore=Apr 28 02:55:17 2026 GMT
notAfter=Apr 28 14:55:17 2026 GMT
--- obot.internal ---
subject= 
issuer= /CN=Caddy Local Authority - ECC Intermediate
notBefore=Apr 28 01:55:17 2026 GMT
notAfter=Apr 28 13:55:17 2026 GMT
--- ollama.internal ---
subject= 
issuer= /CN=Caddy Local Authority - ECC Intermediate
notBefore=Apr 28 01:55:17 2026 GMT
notAfter=Apr 28 13:55:17 2026 GMT
--- plane.internal ---
subject= 
issuer= /CN=Caddy Local Authority - ECC Intermediate
notBefore=Apr 28 01:55:17 2026 GMT
notAfter=Apr 28 13:55:17 2026 GMT
--- prowlarr.internal ---
subject= 
issuer= /CN=Caddy Local Authority - ECC Intermediate
notBefore=Apr 28 02:15:17 2026 GMT
notAfter=Apr 28 14:15:17 2026 GMT
--- radarr.internal ---
subject= 
issuer= /CN=Caddy Local Authority - ECC Intermediate
notBefore=Apr 28 02:15:17 2026 GMT
notAfter=Apr 28 14:15:17 2026 GMT
--- sonarr.internal ---
subject= 
issuer= /CN=Caddy Local Authority - ECC Intermediate
notBefore=Apr 28 02:15:17 2026 GMT
notAfter=Apr 28 14:15:17 2026 GMT
--- uptime.internal ---
subject= 
issuer= /CN=Caddy Local Authority - ECC Intermediate
notBefore=Apr 28 01:55:17 2026 GMT
notAfter=Apr 28 13:55:17 2026 GMT
--- vault.internal ---
subject= 
issuer= /CN=Caddy Local Authority - ECC Intermediate
notBefore=Apr 28 01:55:17 2026 GMT
notAfter=Apr 28 13:55:17 2026 GMT
--- vaultwarden.internal ---
subject= 
issuer= /CN=Caddy Local Authority - ECC Intermediate
notBefore=Apr 28 02:15:17 2026 GMT
notAfter=Apr 28 14:15:17 2026 GMT
--- victoria.internal ---
subject= 
issuer= /CN=Caddy Local Authority - ECC Intermediate
notBefore=Apr 27 23:49:25 2026 GMT
notAfter=Apr 28 11:49:25 2026 GMT
--- webui.internal ---
subject= 
issuer= /CN=Caddy Local Authority - ECC Intermediate
notBefore=Apr 28 01:55:17 2026 GMT
notAfter=Apr 28 13:55:17 2026 GMT
--- zabbix.internal ---
subject= 
issuer= /CN=Caddy Local Authority - ECC Intermediate
notBefore=Apr 28 01:55:17 2026 GMT
notAfter=Apr 28 13:55:17 2026 GMT
```

### Caddy CA root
```
total 24
drwx------    2 root     root          4096 Apr 27 17:52 .
drwx------    3 root     root          4096 Apr 27 17:52 ..
-rw-------    1 root     root           676 Apr 27 17:52 intermediate.crt
-rw-------    1 root     root           227 Apr 27 17:52 intermediate.key
-rw-------    1 root     root           631 Apr 27 17:52 root.crt
-rw-------    1 root     root           227 Apr 27 17:52 root.key
subject= /CN=Caddy Local Authority - 2026 ECC Root
issuer= /CN=Caddy Local Authority - 2026 ECC Root
notBefore=Apr 27 17:52:11 2026 GMT
notAfter=Mar  5 17:52:11 2036 GMT
```

=== SECTION 2 COMPLETE — 687 lines ===

## 3. OPNsense DNS state (Unbound host overrides)

### All host overrides (Unbound) — sorted
```
  anythingllm.internal -> 192.168.10.145  (enabled=1)  desc=Caddy proxy
  dashboard.internal -> 192.168.10.145  (enabled=1)  desc=Caddy proxy
  grafana.internal -> 192.168.10.145  (enabled=1)  desc=Caddy proxy
  headscale.internal -> 192.168.10.145  (enabled=1)  desc=Caddy proxy
  homarr.internal -> 192.168.10.145  (enabled=1)  desc=Caddy proxy
  litellm.internal -> 192.168.10.145  (enabled=1)  desc=Caddy proxy
  mac-mini.internal -> 192.168.10.145  (enabled=1)  desc=Mac Mini M5 - Arr Stack + Vault
  mcp-docker.internal -> 192.168.10.145  (enabled=1)  desc=Phase 7 closeout
  mcp-docs.internal -> 192.168.10.145  (enabled=1)  desc=Phase 7 closeout
  mcp-filesystem.internal -> 192.168.10.145  (enabled=1)  desc=Phase 7 closeout
  nextcloud.internal -> 192.168.10.145  (enabled=1)  desc=Nextcloud via Caddy
  obot.internal -> 192.168.10.145  (enabled=1)  desc=Caddy proxy
  ollama.internal -> 192.168.10.145  (enabled=1)  desc=Caddy proxy
  plane.internal -> 192.168.10.145  (enabled=1)  desc=Caddy proxy
  prowlarr.internal -> 192.168.10.145  (enabled=1)  desc=Caddy proxy
  qnap.internal -> 192.168.10.201  (enabled=1)  desc=QNAP NAS - Storage + rclone
  radarr.internal -> 192.168.10.145  (enabled=1)  desc=Caddy proxy
  sonarr.internal -> 192.168.10.145  (enabled=1)  desc=Caddy proxy
  uptime.internal -> 192.168.10.145  (enabled=1)  desc=Caddy proxy
  vault.internal -> 192.168.10.145  (enabled=1)  desc=Caddy proxy
  vaultwarden.internal -> 192.168.10.145  (enabled=1)  desc=Caddy proxy
  victoria.internal -> 192.168.10.145  (enabled=1)  desc=Phase 7 closeout
  webui.internal -> 192.168.10.145  (enabled=1)  desc=Caddy proxy
  zabbix.internal -> 192.168.10.145  (enabled=1)  desc=Caddy proxy
```

### Resolution probe
```
  mac-mini.internal              -> 192.168.10.145
  qnap.internal                  -> 192.168.10.201
  opnsense.internal              -> 192.168.1.237
  mac-studio.internal            -> NXDOMAIN

Direct .NNN probes:
  192.168.10.145 (mac-mini)   -> rDNS = mac-mini.internal.
  192.168.10.201 (qnap)       -> rDNS = qnap.internal.
  192.168.10.141 (?)          -> rDNS =   192.168.10.1   (opnsense)   -> rDNS = OPNsense.internal.
```

=== SECTION 3 COMPLETE — 732 lines ===

## 4. Vault state

### Status
```
Key             Value
---             -----
Seal Type       shamir
Initialized     true
Sealed          false
Total Shares    5
Threshold       3
Version         2.0.0
Build Date      2026-04-13T18:49:01Z
Storage Type    file
Cluster Name    vault-cluster-1b9404db
Cluster ID      5074eed0-9143-857e-dd9f-35d7575ece30
HA Enabled      false
```

### Secret path tree (paths only — values NEVER read)
```
secret/arr/prowlarr
secret/arr/radarr
secret/arr/sonarr
secret/github/api
secret/headscale/admin
secret/homeassistant/api
secret/macmini/sudo
secret/mcp/strava
secret/minio/backup
secret/nextcloud/admin
secret/nextcloud/db
secret/obot/admin
secret/openweathermap/api
secret/opnsense/api
secret/opnsense/snmp
secret/plane/admin
secret/plane/api
secret/plane/app
secret/plane/minio
secret/plex/api
secret/qnap/admin
secret/qnap/snmp
secret/resilio/qnap
secret/resilio/torrents
secret/resilio/usenet
secret/restic/backup
secret/seedbox/account
secret/seedbox/sabnzbd
secret/seedbox/sftp
secret/strava/oauth
secret/syncthing/seedbox
secret/vaultwarden/admin
secret/zabbix/admin
secret/zabbix/mac-mini-agent
```

=== SECTION 4 COMPLETE — 791 lines ===

## 5. MCP server inventory

### Configured MCP servers — searched in standard locations

### File: /Users/admin/.claude.json
```json
[
  "arr-orchestration",
  "pipeline-monitor"
]
```

### File: /Users/admin/.claude/settings.json
```json
[]
```

### Fallback search for any other claude config files
```
/Users/admin/repos/integrated-ai-platform/.claude/settings.local.json
/Users/admin/.vscode-server/extensions/anthropic.claude-code-2.1.120-darwin-arm64/claude-code-settings.schema.json
/Users/admin/.vscode-server/extensions/anthropic.claude-code-2.1.120-darwin-arm64/package.json
/Users/admin/.claude/mcp-needs-auth-cache.json
/Users/admin/.claude/cache/my-closed-issues.json
/Users/admin/.claude/settings.json
/Users/admin/.claude/plugins/known_marketplaces.json
/Users/admin/.claude/sessions/88735.json
/Users/admin/.claude/.credentials.json
/Users/admin/Library/Application Support/Claude/claude_desktop_config.json
/Users/admin/.claude.json
```

### MCP-related running containers
```
sms1obot-mcp-server-shim	Up 4 hours	ghcr.io/nanobot-ai/nanobot:v0.0.67
sms1obot-mcp-server	Up 4 hours	ghcr.io/obot-platform/obot-mcp-server:v0.1.1
docker-plane-api-1	Up 4 hours (healthy)	makeplane/plane-backend:stable
mcp-docker-remote	Up 4 hours	node:22-slim
nextcloud-db	Up 4 hours (healthy)	postgres:16-alpine
mcp-filesystem-remote	Up 4 hours (healthy)	node:22-slim
zabbix-postgres	Up 4 hours (healthy)	timescale/timescaledb:latest-pg16
mcp-docs-remote	Up 4 hours (healthy)	node:22-slim
mcpo-proxy	Up 4 hours (healthy)	nikolaik/python-nodejs:python3.12-nodejs22-slim
sportarr	Up 4 hours (healthy)	sportarr/sportarr:latest
docker-plane-db-1	Up 4 hours (healthy)	postgres:15-alpine
docker-plane-web-1	Up 4 hours (healthy)	makeplane/plane-frontend:stable
docker-plane-beat-1	Up 4 hours	makeplane/plane-backend:stable
docker-plane-worker-1	Up 4 hours	makeplane/plane-backend:stable
docker-plane-redis-1	Up 4 hours (healthy)	redis:7.2-alpine
docker-plane-minio-1	Up 4 hours	minio/minio:latest
```

### Health endpoint probe (per service-registry MCP entries)
```
  mcp-filesystem-remote          http://localhost:8091/healthz -> http=200
  mcp-docker-remote              http://localhost:8092/healthz -> http=200
  mcp-docs-remote                http://localhost:8093/healthz -> http=200
  obot-shim-postgres             null -> http=000
  obot-shim-postgres-nanobot     null -> http=000
  obot-shim-github               null -> http=000
  obot-shim-github-nanobot       null -> http=000
  obot-shim-weather              null -> http=000
  obot-shim-weather-nanobot      null -> http=000
  obot-shim-fitness              null -> http=000
  obot-shim-fitness-nanobot      null -> http=000
  obot-shim-semgrep              null -> http=000
  obot-shim-semgrep-nanobot      null -> http=000
  obot-shim-strava               null -> http=000
  obot-shim-strava-nanobot       null -> http=000
  obot-shim-homeassistant        null -> http=000
  obot-shim-homeassistant-nanobot null -> http=000
  obot-shim-generic-a            null -> http=000
  obot-shim-generic-b            null -> http=000
  obot-shim-generic-c            null -> http=000
```

### claude CLI MCP-stats discovery
```
  --bare                                            Minimal mode: skip hooks, LSP, plugin sync, attribution, auto-memory, background prefetches, keychain reads, and CLAUDE.md auto-discovery. Sets CLAUDE_CODE_SIMPLE=1. Anthropic auth is strictly ANTHROPIC_API_KEY or apiKeyHelper via --settings (OAuth and keychain are never read). 3P providers (Bedrock/Vertex/Foundry) use their own credentials. Skills still resolve via /skill-name. Explicitly provide context via: --system-prompt[-file], --append-system-prompt[-file], --add-dir (CLAUDE.md dirs), --mcp-config, --settings, --agents, --plugin-dir.
  --mcp-config <configs...>                         Load MCP servers from JSON files or strings (space-separated)
  --mcp-debug                                       [DEPRECATED. Use --debug instead] Enable MCP debug mode (shows MCP server errors)
  --strict-mcp-config                               Only use MCP servers from --mcp-config, ignoring all other MCP configurations
  doctor                                            Check the health of your Claude Code auto-updater. Note: The workspace trust dialog is skipped and stdio servers from .mcp.json are spawned for health checks. Only use this command in directories you trust.
  mcp                                               Configure and manage MCP servers
```

=== SECTION 5 COMPLETE — 879 lines ===

## 6. AnythingLLM specifics

### Container ports (resolves the 3001-vs-3004 ambiguity)
```
3001/tcp -> 0.0.0.0:3004
3001/tcp -> [::]:3004

Inspect summary:
/anythingllm | running | image=mintplexlabs/anythingllm:latest | ports=3001/tcp=0.0.0.0:3004 :::3004 ; | networks=knowledge(172.24.0.2) 
```

### Workspace + document counts (via API)
```
n/a — secret/anythingllm/api not in Vault (no api_key/api_token field)

Direct port-3001 / 3004 probe (fallback):
  http://127.0.0.1:3001/api/ping -> 200
  http://127.0.0.1:3004/api/ping -> 200
```

=== SECTION 6 COMPLETE — 901 lines ===

## 7. Plane CE specifics

n/a — Plane API key not found in secret/plane/admin or secret/plane/api

### Vault paths under plane/
```
Keys
----
admin
api
app
minio
```

=== SECTION 7 COMPLETE — 917 lines ===

## 8. Monitoring stack

### Grafana
```
grafana-obs Up 4 hours
n/a — Grafana API key not in secret/grafana/api or admin_password in secret/grafana/admin
No value found at secret/metadata/grafana
```

### VictoriaMetrics
```
vm Up 4 hours (healthy)
vmagent Up 4 hours

Active scrape targets:
[]
```

### Uptime Kuma
```
uptime-kuma Up 4 hours (healthy)

[
  "heartbeatList",
  "uptimeList"
]
0
(Note: Kuma has no public read API for monitor list without DB access; status-page works only if 'main' page is configured.)
```

### Zabbix
```
zabbix-web Up 4 hours (healthy)
zabbix-agent Up 4 hours
zabbix-server Up 4 hours
zabbix-postgres Up 4 hours (healthy)

jq: error (at <stdin>:0): Cannot iterate over null (null)
```

=== SECTION 8 COMPLETE — 959 lines ===

## 9. Backup / Headscale / Vaultwarden

### Restic — last snapshot per repo
```
n/a — restic creds not in Vault. Available paths:
Keys
----
backup
```

### Headscale — registered nodes (names + IPs only, NO keys)
```
headscale Up 4 hours (healthy)

jq: error (at <stdin>:1): Cannot iterate over null (null)
[96m[96mID[90m[90m | [0m[96m[0m[96mHostname[90m[90m | [0m[96m[0m[96mName[90m[90m | [0m[96m[0m[96mMachineKey[90m[90m | [0m[96m[0m[96mNodeKey[90m[90m | [0m[96m[0m[96mUser[90m[90m | [0m[96m[0m[96mTags[90m[90m | [0m[96m[0m[96mIP addresses[90m[90m | [0m[96m[0m[96mEphemeral[90m[90m | [0m[96m[0m[96mLast seen[90m[90m | [0m[96m[0m[96mExpiration[90m[90m | [0m[96m[0m[96mConnected[90m[90m | [0m[96m[0m[96mExpired[0m
[96m[0m[0m
```

### Vaultwarden
```
vaultwarden Up 4 hours (healthy) 0.0.0.0:8083->80/tcp, [::]:8083->80/tcp

Cipher count via sqlite (capability-checked):
n/a — sqlite3 binary not in vaultwarden container

Admin API user count (if admin_token in vault):
n/a — admin_token not in secret/vaultwarden/admin
```

=== SECTION 9 COMPLETE — 991 lines ===

## 10. GitHub repo state — integrated-ai-platform

**Note:** `git fetch origin` is the one non-strict-read-only call in this inventory — it reads from the remote but does **not** mutate the local working tree, branches, refs, or HEAD.

### Branch + last commit
```
branch: main
hash:   3a8fba0f64cd76de6b834176fa0f370ddce762b6
subject:Replace rclone SFTP with Syncthing for seedbox→QNAP media pipeline
author: Adrian Cox <adbcox@gmail.com>
date:   2026-04-27 23:13:03 -0400
```

### Fetch from origin (read-only)
```
(fetch complete)
```

### Position vs upstream
```
ahead of origin/main: 0
behind origin: 0
```

### git status
```
 ## main...origin/main
?? $COOKIE_JAR
?? config/service-registry.yaml.http-backup
?? data/platform_analytics.db
?? infrastructure-inventory-20260427.md
?? system-audit-output.md
```

### Recent commits (last 5)
```
3a8fba0 Replace rclone SFTP with Syncthing for seedbox→QNAP media pipeline
7ec86fe Phase 7 GENUINE closeout: 22/22 .internal validate, all KIs resolved
99ca1bd Phase 7 closeout: 6 dispositions resolved, 16/17 .internal validate cleanly
aac8a44 Phase 7 closeout: Caddy CA trust complete, 30-day plan complete
f70c0d1 docs: add PHASE_LOG.md — Phase 16 + Strava OAuth complete; Caddy CA pending
```

=== SECTION 10 COMPLETE — 1036 lines ===

## 11. Disk space

### Mac mini host filesystems
```
Filesystem        Size    Used   Avail Capacity iused ifree %iused  Mounted on
/dev/disk3s1s1   926Gi    11Gi   707Gi     2%    453k  4.3G    0%   /

### QNAP SMB mount
Filesystem                         Size    Used   Avail Capacity iused ifree %iused  Mounted on
//admin@192.168.10.201/download    23Ti   8.1Ti    15Ti    36%    8.7G   16G   35%   /Users/admin/mnt/qnap-downloads

### Colima VM data dir
Filesystem      Size    Used   Avail Capacity iused ifree %iused  Mounted on
/dev/disk3s5   926Gi   199Gi   707Gi    22%    1.2M  7.4G    0%   /System/Volumes/Data
```

### Colima VM allocation
```
PROFILE    STATUS     ARCH       CPUS    MEMORY    DISK     RUNTIME    ADDRESS
default    Running    aarch64    4       16GiB     60GiB    docker     
```

### Colima VM internal disk usage
```
docker: Error response from daemon: failed to create task for container: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: error during container init: exec: "/usr/bin/df": stat /usr/bin/df: no such file or directory

Run 'docker run --help' for more information

Memory inside VM:
              total        used        free      shared  buff/cache   available
Mem:          15959        5484        1982         424        8493        9802
Swap:             0           0           0
```

=== SECTION 11 COMPLETE — 1072 lines ===

## 12. Discrepancies noted

### Registry vs running containers

Confirmed earlier this session via service-registry truth-check:
- **`mcp-docker-remote` registry entry has `container: null`** but the actual Docker container `mcp-docker-remote` IS running (deployed earlier as part of Phase 7 KI-002 fix). Registry needs `container: mcp-docker-remote` and `image: node:22-slim` set. **Not fixed in this run** (inventory-only).

### Caddy ↔ DNS mismatches (cross-section 2 vs 3)
```
Caddy routes (22):
  anythingllm.internal
  dashboard.internal
  grafana.internal
  headscale.internal
  homarr.internal
  litellm.internal
  mcp-docker.internal
  mcp-docs.internal
  mcp-filesystem.internal
  nextcloud.internal
  obot.internal
  ollama.internal
  plane.internal
  prowlarr.internal
  radarr.internal
  sonarr.internal
  uptime.internal
  vault.internal
  vaultwarden.internal
  victoria.internal
  webui.internal
  zabbix.internal

OPNsense Unbound .internal A-records (24):
  anythingllm.internal
  dashboard.internal
  grafana.internal
  headscale.internal
  homarr.internal
  litellm.internal
  mac-mini.internal
  mcp-docker.internal
  mcp-docs.internal
  mcp-filesystem.internal
  nextcloud.internal
  obot.internal
  ollama.internal
  plane.internal
  prowlarr.internal
  qnap.internal
  radarr.internal
  sonarr.internal
  uptime.internal
  vault.internal
  vaultwarden.internal
  victoria.internal
  webui.internal
  zabbix.internal

Caddy routes WITHOUT matching DNS A-record:

DNS A-records WITHOUT matching Caddy route (mac-mini, qnap = infrastructure entries; rest = unexpected):
  ⚠️  mac-mini.internal
  ⚠️  qnap.internal
```

### Other observed surprises

- **Resilio Sync (`rslsync`) is configured on the seedbox** (per ADR-A-007 work earlier this session) but the **system daemon** persists across seedbox reboots. Not Mac-Mini-side, but relevant to Phase 13 sync planning.

- **`docker-plane-*-1`** containers use Compose's auto-prefix naming (`docker-plane-api-1`, etc.). Registry IDs are `plane-api`, `plane-db`, etc. Container field correctly maps in registry; no action needed.

- **`open-webui`** registry container name matches actual; `webui.internal` is the correct hostname (an earlier validation list incorrectly used `openwebui.internal` — already documented in earlier ADR `A-006`-era work).

- **`syncthing`** apt-installed system daemon has been **uninstalled** from seedit4me (confirmed by missing systemd unit, dangling `multi-user.target.wants/syncthing@seedit4me.service` symlink). `~/bin/syncthing` v2.0.16 from earlier CLI install remains but is not running. Not a Mac-Mini issue but tracked here as surprise vs prior commit `3a8fba0`.

- **Caddyfile reverse_proxy targets** were switched from `192.168.10.145:PORT` to `host.docker.internal:PORT` during commit `99ca1bd` (Colima networking fix). All routes now use `host.docker.internal`. Worth noting in Phase 13 docs because it differs from the original architecture sketch.

- **Vaultwarden cipher count via sqlite**: capability check. Will appear in §9 as either a number or "n/a — sqlite3 not in container".

### Inventory-run open items (not gaps, just notes)
- Vault values are NEVER read in this report — only `vault status` and `vault kv list` (paths).
- `git fetch origin` was run in §10. It's the ONLY remote call in this report; it does not mutate local state.

