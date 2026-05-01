# Syncthing seedbox→QNAP — operational runbook

**Status**: Active operational runbook for the Syncthing transfer pipeline.
**Captures**: Phase 15 operational lessons + post-2026-04-28 reinstall state.
**Decision context**: See `docs/adr/ADR-A-007-media-sync-syncthing.md` for the original decision (Accepted 2026-04-27). This runbook supplements that ADR with operational truth that does not belong in a decision record.

---

## Topology

| Side | Host | Sync listener | GUI | Config path |
|---|---|---|---|---|
| Source | seedbox `5.nl19.seedit4.me` | `tcp://0.0.0.0:26401` | `0.0.0.0:8384` | `/home/seedit4me/.config/syncthing/config.xml` |
| Destination | QNAP `192.168.10.201` | default | `http://192.168.10.201:8384` | `/share/CACHEDEV1_DATA/.qpkg/SyncThing/config.xml` |

Two folders synchronized:

- `sabnzbd-complete` (`is5fj-3grur`): seedbox `~/sabnzbd/complete/` (sendonly) → QNAP `/share/CACHEDEV2_DATA/download/sabnzbd/` (receiveonly), `ignoreDelete=false`
- `torrents-rtorrent` (`3qukn-rfdel`): seedbox `~/torrents/rtorrent/` (sendonly) → QNAP `/share/CACHEDEV2_DATA/download/rtorrent/` (receiveonly), `ignoreDelete=true` to preserve seeding obligations

SSH access to seedbox is on port 2088 (see `connectors/seedbox.py`).

---

## Credentials

API keys and device IDs for both Syncthing instances are operational secrets. They are intentionally NOT recorded in this runbook. They live in (and should be retrieved from) the configuration files on each side:

- Seedbox: `/home/seedit4me/.config/syncthing/config.xml`
- QNAP: `/share/CACHEDEV1_DATA/.qpkg/SyncThing/config.xml`

**Pending migration to Vault** (blocked on D-15-04 / R-02 — Vault audit device must be re-enabled before new secrets are written so the writes are logged). Once R-02 closes, provision and migrate credentials to:

- `secret/syncthing/seedbox` — fields: `api_key`, `device_id`, `hostname`, `gui_bind`, `sync_listener`
- `secret/syncthing/qnap` — fields: `api_key`, `device_id`, `web_url`, `config_path`

After the migration, both this runbook and ADR-A-007 are amended to reference Vault paths instead of config-file paths, and any inline credentials are removed from A-007 (separate change record).

---

## Reinstall procedure

Triggered when the seedbox `~/bin/syncthing` binary is removed, replaced, or corrupted. Last invocation: 2026-04-28.

### 1. Verify port 26401 is free on the seedbox

The host system service `resilio-sync.service` (`rslsync`) historically binds port 26401 and conflicts with Syncthing's sync listener. If `resilio-sync` is `active (running)` when Syncthing starts, Syncthing fails silently with no log entry. Verify the port is free:

```
systemctl status resilio-sync
systemctl is-enabled resilio-sync
```

Expected: `inactive (dead)` and `disabled` (or `masked`). If active or enabled:

```
systemctl stop resilio-sync
systemctl disable resilio-sync
```

### 2. Confirm Syncthing binary

```
ls -la ~/bin/syncthing
~/bin/syncthing --version
```

If missing or corrupted, redeploy from upstream releases (https://github.com/syncthing/syncthing/releases) and verify checksum before launch.

### 3. Launch and verify

```
~/bin/syncthing serve --no-browser &
```

Confirm GUI reachable at `http://0.0.0.0:8384` (via SSH port-forward `-L 8384:127.0.0.1:8384` if remote management).

### 4. Restore @reboot crontab entry

The seedbox has no systemd unit for Syncthing — the previous unit was uninstalled, and only the user-mode `~/bin/syncthing` binary remains. Process-level supervision is via crontab:

```
@reboot ~/bin/syncthing serve --no-browser &
```

Verify the crontab entry exists with `crontab -l`. If missing, re-add via `crontab -e`.

### 5. Re-pair devices

If device IDs changed during reinstall, re-pair both sides via the GUI. Old device IDs in `remoteSequence` (e.g., the pre-2026-04-28 `FIOKLLV-...` identity that may persist on QNAP) are harmless once disconnected; remove them from QNAP device list when convenient.

---

## Known failure modes

### F1 — No process supervisor on seedbox

The seedbox-side Syncthing daemon runs without systemd or any other supervisor — only `~/bin/syncthing` plus the `@reboot` crontab entry. **If the daemon dies mid-session, transfers stop silently without auto-restart.**

Mitigation:
- Operator-side: monitor folder sync status periodically via the GUI.
- Future: a Syncthing event-listener probe (`/rest/events?events=ItemFinished`) could trigger an alert via Zabbix. Not yet implemented; tracked as a follow-up.

### F2 — Resilio-sync port collision (2026-04-28 incident)

On 2026-04-28 the host system service `resilio-sync` (`rslsync`) was started by the seedit4me hosting provider and bound port 26401 — the port Syncthing was configured for. Syncthing failed to start; no error logged anywhere visible to the operator.

Mitigation:
- `resilio-sync.service` is stopped and disabled. Verify periodically with `systemctl is-enabled resilio-sync` (expected: `disabled` or `masked`).
- If `rslsync` ever returns to an enabled state without operator action, treat it as an incident, re-disable, and investigate provider-side configuration drift.

### F3 — SMB orphan `.smbdelete*` files

The QNAP-side `sabnzbd-complete` folder is `receiveonly`. When Sonarr completes an import-by-move via SMB, the original `.mkv` is moved out from under Syncthing, leaving `.smbdelete*` orphan files in `/share/CACHEDEV2_DATA/download/sabnzbd/`.

Treatment: these are cleanable garbage; they do not block the import pipeline.

Mitigation: add `.smbdelete*` to `.stignore` on both Syncthing folders to suppress them at sync time. Until that is done, periodic cleanup of orphan files is acceptable.

---

## Rollback to rclone (per ADR-A-007)

If Syncthing fails persistently and rclone needs to be reactivated:

1. Pause both Syncthing folders on the QNAP side via REST API:
   ```
   POST /rest/folder/pause?folder=is5fj-3grur
   POST /rest/folder/pause?folder=3qukn-rfdel
   ```
2. Restart the rclone containers on QNAP:
   ```
   docker start rclone-sabnzbd rclone-mover
   ```
3. The rclone configuration is unchanged from pre-Syncthing era and ready to resume.

Throughput impact: ~250 KiB/s ceiling vs. ~136 Mbps Syncthing average (~68x slower). Use only as a last-resort fallback.

---

## References

- `docs/adr/ADR-A-007-media-sync-syncthing.md` — original decision (Accepted 2026-04-27)
- `connectors/seedbox.py` — seedbox connector with SSH port + paths
- `docs/PROJECT_FRAMEWORK.md` — closes D-15-07 / Phase 15
- Syncthing documentation: https://docs.syncthing.net/
