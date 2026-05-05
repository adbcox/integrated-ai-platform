# Media stack naming doctrine (D-17-114)

## Canonical names

- `plex.internal` is the canonical LAN name for the Plex Media Server on QNAP `192.168.10.201:32400`.
- `plex-mcp.internal` is a separate MCP control surface on the Mac Mini at `host.docker.internal:8094`.

Do not treat `plex-mcp.internal` as the media server. It is the agent integration surface only.

## Access posture

For LAN clients, Plex should resolve and reverse-proxy through `plex.internal` rather than falling back to GDM discovery or `plex.tv` relay paths.

Expected substrate:

- Dnsmasq host record: `plex.internal -> 192.168.10.201`
- Caddy site block: `plex.internal -> 192.168.10.201:32400`
- Plex server `Custom server access URLs`: `https://plex.internal:443,http://192.168.10.201:32400`

## Credential path

Plex credentials live at `secret/plex/api`.

Hash-only handling applies to token values in transcripts and surfaces.
