# Seedbox Apps Setup Guide

Installation and configuration guide for apps on the seedbox. Run these steps over SSH or via the seedbox provider's web terminal.

---

## Overview

| App | Reason | Required? |
|-----|--------|-----------|
| **rclone** | Syncs completed downloads from seedbox to QNAP automatically | **CRITICAL** |
| **Flood** | Web UI for rTorrent — monitor downloads, verify blackhole activity | Recommended |
| **Autobrr** | IRC announce monitoring for instant grabs from trackers | Optional / Advanced |
| Sonarr | TV show management | DO NOT INSTALL |
| Radarr | Movie management | DO NOT INSTALL |
| Plex / Jellyfin | Media streaming server | DO NOT INSTALL |
| Syncthing | File sync daemon | DO NOT USE |
| qBittorrent / Deluge | Alternative torrent clients | DO NOT INSTALL |

Install in the order listed above. rclone must be working before anything else matters.

---

## SSH Access

```bash
ssh -p 2088 seedit4me@193.163.71.22
```

Alternatively, use the seedbox provider's built-in web terminal if SSH from your local machine is blocked.

Once connected, verify your environment:

```bash
# Check your home directory
pwd
# Should be /home/seedit4me

# Verify rTorrent is running
pgrep rtorrent && echo "rTorrent: running" || echo "rTorrent: NOT running"

# Check the blackhole directory exists
ls /home/seedit4me/rwatch/

# Check the downloads directory
ls /home/seedit4me/torrents/rtorrent/ | head -10
```

---

## rclone Setup (CRITICAL — Do This First)

rclone is the bridge that moves completed downloads from the seedbox to QNAP. Without it, files pile up on the seedbox and never reach Sonarr/Radarr for import.

### Step 1: Check if rclone is already installed

```bash
rclone version
```

If it prints a version number, skip to Step 3. If you get "command not found", continue with Step 2.

### Step 2: Install rclone

**Option A — Seedbox app manager (preferred if available):**
Log in to your seedbox provider's control panel, find the app installer, and install rclone from there. This ensures it is installed in a supported location with correct permissions.

**Option B — Manual install:**
```bash
curl https://rclone.org/install.sh | sudo bash
```

If `sudo` is not available on your seedbox:
```bash
mkdir -p ~/bin
curl -O https://downloads.rclone.org/rclone-current-linux-amd64.zip
unzip rclone-current-linux-amd64.zip
cp rclone-*-linux-amd64/rclone ~/bin/rclone
chmod +x ~/bin/rclone
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

Verify the install:
```bash
rclone version
```

### Step 3: Configure an rclone remote for QNAP

Run the interactive config wizard:

```bash
rclone config
```

Follow these prompts:

```
No remotes found, make a new one? → n (new remote)
name> qnap
Type of storage> sftp
  (enter the number for "SSH/SFTP")
host> 192.168.10.201
user> admin
port> 22
password> (enter QNAP admin password — will be stored encrypted)
key_file> (leave blank unless using SSH key auth)
key_file_pass> (leave blank)
pubkey_file> (leave blank)
known_hosts_file> (leave blank)
key_use_agent> false
use_insecure_cipher> false
disable_hashcheck> false
Edit advanced config? → n
```

When done, your config will show a remote named `qnap`.

### Step 4: Test the connection

```bash
rclone ls qnap:/share/download/
```

This should list files in QNAP's download share. If you get an error:
- Verify QNAP has SFTP enabled: Control Panel → Terminal & SNMP → Enable SSH service
- Verify the admin password is correct
- Verify QNAP is reachable from the seedbox: `ping 192.168.10.201`

### Step 5: Create the sync script

```bash
cat > /home/seedit4me/sync_to_qnap.sh << 'EOF'
#!/bin/bash
rclone sync /home/seedit4me/torrents/rtorrent/ qnap:/share/download/ \
  --log-file=/home/seedit4me/rclone.log \
  --log-level INFO \
  --exclude "*.part" \
  --transfers 4 \
  --checkers 8 \
  --min-age 5m
EOF

chmod +x /home/seedit4me/sync_to_qnap.sh
```

Script parameters explained:
- `--exclude "*.part"` — skips incomplete/in-progress files so only finished downloads sync
- `--transfers 4` — 4 parallel file transfers (increase to 8 if QNAP and seedbox can handle it)
- `--checkers 8` — 8 parallel checksum workers (safe to increase)
- `--min-age 5m` — only syncs files at least 5 minutes old (extra safety buffer against partial files)
- `--log-file` / `--log-level INFO` — full log for debugging

### Step 6: Test the sync script manually

```bash
bash /home/seedit4me/sync_to_qnap.sh
echo "Exit code: $?"
tail -20 ~/rclone.log
```

The first run may take a while if there are many files. Subsequent runs are incremental (only transfers new/changed files).

### Step 7: Add the crontab entry

```bash
crontab -e
```

Add this line (runs every 15 minutes):
```
*/15 * * * * bash /home/seedit4me/sync_to_qnap.sh
```

Save and exit the editor.

### Step 8: Verify the crontab

```bash
crontab -l | grep sync
```

Expected output:
```
*/15 * * * * bash /home/seedit4me/sync_to_qnap.sh
```

### Step 9: Monitor the log

After waiting ~15 minutes for the first cron run:

```bash
tail -f ~/rclone.log
```

A healthy log looks like:
```
2026/04/25 14:00:01 INFO  : Show.Name.S01E01/episode.mkv: Copied (new)
2026/04/25 14:00:02 INFO  : Movie.Name.2024/movie.mkv: Copied (new)
2026/04/25 14:00:02 INFO  :
Transferred:   12.345 GBytes in 1m30s, 140 MBytes/s
Errors:        0
Checks:        147
Transferred:   2
Elapsed time:  1m30s
```

---

## Flood Setup (Recommended)

Flood is a modern web UI for rTorrent. It provides a clean interface for monitoring active torrents, checking download progress, and verifying the blackhole is being watched — all from a browser. The Mac Mini AI dashboard can query Flood's REST API to surface torrent status.

### What Flood is

Flood sits on top of rTorrent (which is already running on your seedbox) and provides:
- A clean browser UI at `http://193.163.71.22:3000`
- A REST API for programmatic torrent status queries
- Real-time speed and progress tracking

### Option A: Install via seedbox app manager (preferred)

Most managed seedbox providers include Flood in their app catalog. Log in to the control panel, find Flood, and install it. The provider will handle the rTorrent socket path configuration automatically.

Note the port it is installed on (typically 3000 or a provider-assigned port).

### Option B: Manual install

Flood requires Node.js 16 or newer.

```bash
# Check Node.js version
node --version

# If not installed or too old, install via nvm:
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc
nvm install 20
nvm use 20

# Install Flood globally
npm install -g flood

# Find the rTorrent socket path (your provider will have set this)
# Common locations:
#   /home/seedit4me/.sessions/rTorrent.sock
#   /tmp/rtorrent.sock
#   /var/run/rtorrent/rtorrent.sock
ls ~/.sessions/*.sock 2>/dev/null || find /tmp -name "*.sock" 2>/dev/null | head -5

# Start Flood (replace socket path with your actual socket)
flood --auth none --rtorrent-socket /home/seedit4me/.sessions/rTorrent.sock
```

To run Flood persistently in the background, use a process manager or a screen session:

```bash
# Using screen
screen -dmS flood flood --auth none --rtorrent-socket /home/seedit4me/.sessions/rTorrent.sock

# Or using nohup
nohup flood --auth none --rtorrent-socket /home/seedit4me/.sessions/rTorrent.sock \
  > ~/flood.log 2>&1 &
```

### Access and API token

- Browser: `http://193.163.71.22:3000` (or your provider-assigned port)
- API token: Settings → Auth → Create API token (used by the AI platform dashboard)

### Dashboard integration

The Mac Mini monitoring dashboard shows the seedbox Flood API as "Flood" in the media stack panel. Once Flood is running, update the dashboard configuration with the Flood URL and API token.

---

## Autobrr Setup (Optional / Advanced)

Autobrr monitors IRC announce channels for torrent trackers and grabs releases the moment they are announced — often seconds after upload, before RSS feeds update. Use this only if you are on private trackers that support IRC announce and you want first-grab speed.

### When to use Autobrr

- You are on competitive private trackers where ratios depend on grabbing quickly
- You want Sonarr/Radarr to have releases available before the standard RSS polling interval
- You have IRC credentials for your tracker's announce channel

### Install

```bash
# Download the latest release
wget https://github.com/autobrr/autobrr/releases/latest/download/autobrr_linux_amd64.tar.gz

# Extract
tar xf autobrr_linux_amd64.tar.gz

# Move to ~/bin
mkdir -p ~/bin
mv autobrr ~/bin/autobrr
chmod +x ~/bin/autobrr

# Create config directory
mkdir -p ~/.config/autobrr

# Start (it will generate a default config on first run)
~/bin/autobrr --config ~/.config/autobrr/
```

Autobrr runs on port `7474` by default. Access it at `http://193.163.71.22:7474`.

### Connect to Sonarr/Radarr

In the Autobrr web UI:
1. Settings → Download Clients → Add
2. Choose type: Sonarr (or Radarr)
3. Host: `192.168.10.201`, Port: `8989` (Sonarr) or `7878` (Radarr)
4. API Key: copy from Sonarr/Radarr → Settings → General → API Key
5. Save and test the connection

### Add IRC announce feeds

1. Settings → IRC Networks → Add
2. Enter your tracker's IRC server, port, and channel
3. Enter your IRC nickname and NickServ password
4. Save

Then create Filters to match specific releases and route them to Sonarr/Radarr or directly to the rTorrent blackhole.

### Run Autobrr persistently

```bash
nohup ~/bin/autobrr --config ~/.config/autobrr/ > ~/autobrr.log 2>&1 &
```

Or add a startup script via the seedbox provider's process manager if available.

---

## DO NOT Install These

### Sonarr / Radarr
Already running on QNAP. Installing a second instance on the seedbox creates split-brain: two databases tracking the same torrents, two sets of rename rules, conflicting import actions. All media management stays on QNAP.

### Plex / Jellyfin
The media library is organized on QNAP and served from QNAP. Installing a streaming server on the seedbox means streaming raw (unorganized) files over datacenter bandwidth to your home, which is both slower and defeats the purpose of having the QNAP serve media on the local network. It also violates most seedbox acceptable-use policies.

### Syncthing
Syncthing has no native `.part` file exclusion — it will sync incomplete files mid-download, causing Sonarr/Radarr to pick up corrupt files. rclone's `--exclude "*.part"` and `--min-age` flags handle this correctly. Do not replace rclone with Syncthing.

### qBittorrent / Deluge
rTorrent is already installed and configured by the seedbox provider. Adding a second torrent client causes port conflicts, duplicate downloads, and split watch directories. The blackhole setup is built around rTorrent's watch directory (`rwatch`). Do not add another client.

---

## Verify Everything Works

Run this verification checklist after completing setup:

```bash
# Check rTorrent is running
pgrep rtorrent && echo "rTorrent: running" || echo "rTorrent: NOT RUNNING"

# Check blackhole is being watched
ls /home/seedit4me/rwatch/
# (empty is fine — it means no pending .torrent files)

# Check recent downloads
ls -lht /home/seedit4me/torrents/rtorrent/ | head -20

# Check rclone is working (view last 20 log lines)
tail -20 ~/rclone.log

# Test a manual sync right now
bash /home/seedit4me/sync_to_qnap.sh && echo "Sync OK" || echo "Sync FAILED"

# Check crontab is configured
crontab -l
# Should show the */15 sync line

# Verify rclone can reach QNAP
rclone lsd qnap:/share/download/ && echo "QNAP reachable" || echo "QNAP unreachable"
```

Expected results:
- rTorrent is running
- `/home/seedit4me/rwatch/` exists (may be empty)
- `/home/seedit4me/torrents/rtorrent/` contains your downloaded content
- `rclone.log` shows recent transfers or "0 bytes transferred" (if nothing new)
- Manual sync exits 0
- `crontab -l` shows `*/15 * * * * bash /home/seedit4me/sync_to_qnap.sh`
- QNAP remote is reachable

If any check fails, refer to the troubleshooting section in `SEEDBOX_QNAP_ARCHITECTURE.md`.
