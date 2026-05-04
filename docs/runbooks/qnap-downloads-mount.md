# QNAP `download` SMB mount — runbook

**Status:** Interim. Mount works in-session as of 2026-05-03 09:30 local. Persistence work is **blocked behind Finding Y** (see `docs/_audit/integrated-stack-gaps-2026-05-03.md` Gap X2). Execute the Persistence steps below only after Finding Y resolves.

**Owner:** operator (mount target on Mac Mini control plane).

**Related artifacts:**
- Finding Y context: `docs/_audit/integrated-stack-gaps-2026-05-03.md` Gap X2; D-17-29 closeout note in `docs/PROJECT_FRAMEWORK.md` §9.
- Recurring-pain-point cross-reference: Gap F8 in `docs/_audit/integrated-stack-gaps-2026-05-03.md`.
- Pending-followup trigger: `~/Documents/pending-platform-followups.md` → "QNAP SMB mount LaunchDaemon persistence".
- Syncthing pipeline that populates the share: `docs/runbooks/syncthing-rebuild.md`.

---

## What this mount is for

The QNAP NAS at `192.168.10.201` exports an SMB share named `download` whose backing path is `/share/CACHEDEV2_DATA/download` (presented as `/share/download/`). Syncthing replicates seedbox `~/sabnzbd/complete/` and `~/torrents/rtorrent/` into that share.

The arr-stack (`sonarr`, `radarr`) on the Mac Mini binds `/Users/admin/mnt/qnap-downloads → /downloads` inside each container. The `/downloads/sabnzbd/<svc>/` and `/downloads/rtorrent/` paths inside the container are the targets of every Sonarr/Radarr remote-path-mapping. Without the SMB mount, `/Users/admin/mnt/qnap-downloads` is an empty APFS directory and every import fails with `path does not exist or is not accessible`.

Both arr containers also bind `/Users/admin/mnt/qnap-downloads/data → /data`, which surfaces QNAP's `/share/download/data → /share/CACHEDEV2_DATA/data` symlink. That tree carries `/data/media/{tv,movies,sports}` — the Sonarr / Radarr root folders.

---

## Manual mount (current in-session state)

```bash
mount_smbfs '//admin:<password>@192.168.10.201/download' /Users/admin/mnt/qnap-downloads
```

Notes verified 2026-05-03:
- **No `sudo` required.** `/Users/admin/mnt/qnap-downloads` is owned by `admin:staff` and `mount_smbfs` accepts user-domain mounts on macOS 15+.
- **No `rm -rf` of the mount point.** It currently contains `audit-archive/`, `data/`, `sports/`. SMB mount overlays them cleanly; the local content is hidden, not deleted.
- **Mount survives until** logout, sleep-induced eviction, or `umount`. **Does not survive reboot** until the LaunchDaemon is loaded.
- **Container restart required** after a new mount: Docker Desktop's filesystem bridge does not pick up a mount overlaid onto an existing bind path; existing containers continue to see the empty pre-mount directory until restarted. `docker restart sonarr radarr`.
- **SMB negotiated SMB 3.1.1, AES_128_GMAC signing, encryption available but currently OFF.** Files surface to host as `admin:staff`; **inside the container they appear as `root:root` mode 0700** for files originally owned by `admin` on QNAP. Files originally owned by `syncthing` (uid 1000) on QNAP surface readable. Sonarr's import-by-move via SMB (runbook F3 in `syncthing-rebuild.md`) succeeds in either case because the move operation is performed by the SMB client at the protocol level, not via UNIX-style read+write+unlink.

---

## Persistence — EXECUTE WHEN FINDING Y RESOLVES

> **Pre-flight gate.** Run the Finding Y check from `~/Documents/pending-platform-followups.md` first. If `sudo launchctl print system/com.iap.platform-registry` succeeds (or any other `com.iap.*` daemon is loaded in system domain), Y is resolved and you may proceed. If system-domain launchd entries are missing, **stop and surface back** before adding this mount job.

### Step 1 — Store the SMB password in the user keychain

Doctrine: secrets-not-on-disk. The plist itself contains no password.

```bash
security add-internet-password \
  -a "admin" \
  -s "192.168.10.201" \
  -P 445 \
  -r "smb " \
  -l "QNAP SMB Mount (com.iap.qnap-downloads-mount)" \
  -T /sbin/mount_smbfs \
  -w '<password>'
```

Field explanation:
- `-a admin` — account name (matches the SMB user).
- `-s 192.168.10.201` — server (matches the SMB host).
- `-P 445` — port (must match what `mount_smbfs` will use).
- `-r "smb "` — protocol code (4 chars including trailing space — required form for SecKeychain SMB lookups).
- `-T /sbin/mount_smbfs` — authorize `mount_smbfs` to read this item without prompting. **Critical:** without this, the LaunchDaemon will hang on first invocation waiting for a keychain prompt that never appears under launchd.
- `-l` — display label, easy to find in Keychain Access.

Verify:

```bash
security find-internet-password -a admin -s 192.168.10.201 -g 2>&1 | grep -E '^(class|attributes|"prot"|"acct"|"srvr"|"port")' | head -8
```

(`-g` will surface the password to stderr only when an interactive operator approves the keychain dialog — do not run this automated. Use `find-internet-password` without `-g` for a quiet existence check.)

### Step 2 — Create the LaunchDaemon plist

Path: `docker/launchd-agents/com.iap.qnap-downloads-mount.plist` (repo source), install target `/Library/LaunchDaemons/com.iap.qnap-downloads-mount.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.iap.qnap-downloads-mount</string>

    <key>ProgramArguments</key>
    <array>
        <string>/sbin/mount_smbfs</string>
        <string>//admin@192.168.10.201/download</string>
        <string>/Users/admin/mnt/qnap-downloads</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <false/>

    <key>StandardOutPath</key>
    <string>/Users/admin/.platform-registry/qnap-mount.stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/admin/.platform-registry/qnap-mount.stderr.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
```

Notes:
- **No password in plist.** `mount_smbfs` will retrieve it from the keychain entry created in Step 1 because the keychain item's `acct=admin / srvr=192.168.10.201 / port=445 / prot="smb "` quartet matches the URL.
- **`KeepAlive=false`.** This is a one-shot at login — relaunching `mount_smbfs` after it exits 0 would attempt to mount over an already-mounted path and fail.
- **No `WatchPaths`.** macOS does not reliably surface SMB mount-loss as a filesystem event; auto-remount on disconnect is out of scope for this plist. If you need that, layer a separate watchdog agent or move to autofs.
- **Logs land under `~/.platform-registry/`** to keep all com.iap.* agents' output in one place (matches existing convention from `com.iap.platform-registry.plist`).

### Step 3 — Bootstrap the daemon

```bash
# Sanity check — Finding Y must be resolved first
sudo cp docker/launchd-agents/com.iap.qnap-downloads-mount.plist /Library/LaunchDaemons/
sudo launchctl bootstrap system /Library/LaunchDaemons/com.iap.qnap-downloads-mount.plist
echo "exit=$?"
```

Expect exit 0. If bootstrap fails, **abort and re-check launchd domain/status** — do not retry-loop.

### Step 4 — Verify

```bash
# 1. Plist is registered
launchctl list | grep com.iap.qnap-downloads-mount

# 2. Mount is live
mount | grep qnap-downloads
ls /Users/admin/mnt/qnap-downloads/sabnzbd/sonarr/ | head -3

# 3. Containers see content
docker exec sonarr ls /downloads/sabnzbd/sonarr/ | head -3
docker exec radarr ls /downloads/sabnzbd/radarr/ | head -3
```

### Step 5 — Refresh service registry

```bash
~/.platform-registry/refresh.sh
# OR if not yet on PATH:
/Users/admin/repos/integrated-ai-platform/scripts/platform-registry/refresh.sh
```

The refresh picks up the new LaunchDaemon as a platform dependency. Confirm by inspecting `~/.platform-registry/inventory.json` for an entry tied to `com.iap.qnap-downloads-mount`.

### Step 6 — Restart arr containers (if mount was newly established by the agent)

```bash
docker restart sonarr radarr
sleep 12
curl -s http://localhost:8989/api/v3/health -H "X-Api-Key: <SONARR_KEY>" | python3 -m json.tool
curl -s http://localhost:7878/api/v3/health -H "X-Api-Key: <RADARR_KEY>" | python3 -m json.tool
```

Expect `RemotePathMappingCheck` and `RootFolderCheck` errors absent. The 1337x indexer warning (Prowlarr) and Radarr's TMDb/MovieCollectionRootFolder cosmetic errors are unrelated and pre-existing.

---

## Rollback

```bash
sudo launchctl bootout system/com.iap.qnap-downloads-mount
umount /Users/admin/mnt/qnap-downloads
sudo rm /Library/LaunchDaemons/com.iap.qnap-downloads-mount.plist
# Optionally remove the keychain entry:
security delete-internet-password -a admin -s 192.168.10.201 -P 445 -r "smb "
```

The arr containers will continue to run with an empty `/downloads` until the next mount is established or until they're stopped.

---

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `Bootstrap failed: 5: Input/output error` | System-domain install/bootstrap failed or plist invalid. | Validate plist + ownership/permissions, then retry bootstrap once. |
| Plist loads but mount is empty inside the container | Mount established *after* the container was created; bind layer is frozen. | `docker restart sonarr radarr`. |
| Container shows files as `root:root 0700`, Sonarr cannot read them | macOS smbfs ↔ Docker Desktop file-bridge UID translation gap; only files owned by `admin` (uid 502) on QNAP are affected. Files owned by `syncthing` (uid 1000) surface readable. | Sonarr's SMB-side import-by-move (`.smbdelete*` artifacts per `syncthing-rebuild.md` F3) usually succeeds anyway. If imports fail wholesale, normalize ownership on QNAP: `ssh admin@192.168.10.201 'chown -R syncthing:everyone /share/download/sabnzbd/ /share/download/rtorrent/'`. |
| Mount succeeds but `/data/media/...` is missing inside container | QNAP-side `/share/download/data` symlink not followed. SMB clients on macOS handle symlinks via the `mfsymlinks` extension which QNAP supports out of the box. | Verify with `ls -la /Users/admin/mnt/qnap-downloads/data/` on host — if it's an empty dir not a symlink-traversed tree, the QNAP-side symlink is broken; investigate on QNAP. |
| Mount loss after Mac sleep/wake | macOS SMB client does not auto-reconnect after extended idle. | Manual `umount` + re-bootstrap, or implement a watchdog agent (out of scope here). |

---

## Why this is its own runbook (and not folded into add-new-service)

`docs/runbooks/add-new-service.md` covers Vault Agent + container service onboarding. This is a **host-level filesystem dependency** that any number of containers transitively rely on. Kept separate so that any future host-level mount (a second QNAP share, a Linux/Threadripper migration mount, etc.) has a template.
