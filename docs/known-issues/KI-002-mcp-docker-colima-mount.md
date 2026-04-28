# KI-002: mcp-docker MCP server runtime issues

## Status
RESOLVED — proper Docker container `mcp-docker-remote` runs node:22-slim with supergateway + mcp-server-docker, mounts `/var/run/docker.sock` from the Linux VM (not the un-mountable macOS host path), listens IPv4 on 0.0.0.0:8092. Reachable via Caddy at https://mcp-docker.internal/healthz with verify=0 http=200.

## Root cause stack

### 1. Container cannot start
`docker start mcp-docker-remote` fails:
```
error while creating mount source path '/Users/admin/.colima/default/docker.sock':
mkdir /Users/admin/.colima/default/docker.sock: operation not supported
```
Cause: the compose spec mounts a host-side path that is a Unix socket file, but
Colima cannot bind-mount a socket file across the VM boundary.

### 2. Host-side workaround binds IPv6-only
Running mcp-server-docker via host `npx supergateway` produces an IPv6-only
listener (`node ... TCP *:8092 IPv6 LISTEN`). On Colima, dual-stack IPv6
bindings work for connections from the same host but reverse_proxy from the
Caddy container via the LAN IP `192.168.10.145:8092` times out — the
container's IPv4 stack cannot reach an IPv6-only listener on the LAN IP.

### 3. supergateway --host flag does not exist
`npx supergateway --host 0.0.0.0` is silently ignored; the listener is still
IPv6-only.

## Direct verification status
- `curl http://host.docker.internal:8092/healthz` from a sibling container: **200 OK**
- `wget http://192.168.10.145:8092/healthz` from inside Caddy container: **timeout**
- The MCP server itself responds correctly when reached on a path Colima's NAT can route.

## Permanent fix options
1. **Force IPv4 binding** — wrap supergateway with a Node script that binds
   the http server explicitly to `0.0.0.0`. supergateway 3.4 does not expose
   this flag.
2. **Switch to mcp-server-docker via socat** — `socat TCP-LISTEN:8092,fork,reuseaddr,bind=0.0.0.0`
   in front of an IPv6-bound supergateway. Adds a process but solves the gap.
3. **Caddy route to host.docker.internal:8092** — works for reachability but
   only valid inside Colima's internal DNS; would not work for LAN clients
   resolving via OPNsense Unbound (LAN clients hit Caddy on LAN IP first, so
   the upstream is internal-only and this is actually fine).
4. **Switch from Colima to Docker Desktop** — Docker Desktop bind-mounts
   docker.sock natively; the original docker container would just work.

## Created
Mon Apr 27 20:08:25 EDT 2026
