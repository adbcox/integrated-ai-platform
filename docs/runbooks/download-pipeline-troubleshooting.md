# Download Pipeline Troubleshooting

Date: 2026-05-04
Primary monitoring substrate: Zabbix 7.4
Deliverable: D-17-105

## Quick triage order

1. Check Zabbix items on host `mac-mini` with key prefix `d17105.`.
2. If arr queue grows (`*.queue_depth`), inspect corresponding arr `/api/{v1|v3}/queue`.
3. If arr health count >0, inspect `/api/{v1|v3}/health` details first.
4. If SAB queue grows, check SAB category routing per app (`sonarr`, `radarr`, `lidarr`).
5. If imports stall with healthy queues, validate remote path mappings and container mounts.

## Common failure patterns

1. **Wrong category segregation**
   - Symptom: one app sees another app’s queue items.
   - Fix: verify download-client category matches app name exactly.

2. **Remote path mismatch**
   - Symptom: health warnings about non-existent completed-download path.
   - Fix: align seedbox remote path and container local path in arr remote path mappings.

3. **False healthy container**
   - Symptom: container health checks green but imports fail.
   - Fix: trust `d17105.*` item outcomes over container liveness.

## Provisioning / reapply

Run:

```bash
scripts/provision-zabbix-download-pipeline.sh
```

This updates macros/items/triggers idempotently for current arr + SAB surfaces.

## Pending integrations

- Syncthing stage monitors remain pending until Vault paths are restored:
  - `secret/syncthing/seedbox`
  - `secret/syncthing/qnap`

- rTorrent stuck-torrent count requires dedicated RPC probe integration.
