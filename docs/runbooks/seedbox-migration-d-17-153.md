# Runbook: D-17-153 Seedbox Migration to Whatbox NL

**Status:** DRAFT v0.1 — operator-reviewed before first use
**Created:** 2026-05-07 (flight session)
**Master plan:** `docs/decision-records/D-17-MEDIA-master-plan.md`
**Covers:** WP-153-01 through WP-153-04 (the first 90 minutes of execution at home)

---

## Purpose

Migrate from seedit4me (Hetzner Falkenstein, Germany) to Whatbox NL (Amsterdam) to fix the BGP routing bottleneck (~10 Mbps direct currently) without losing throughput or downtime.

## Pre-flight checklist

**MUST be true before starting:**
- [ ] You're at home on the Comcast WAN (need to test from your actual home IP)
- [ ] Mac Mini is reachable (or you're working entirely from QNAP/MacBook)
- [ ] Vault is unsealed (you'll store new seedbox creds there)
- [ ] You have a credit card / payment method ready
- [ ] Current seedit4me account is active and paid through this calendar month
- [ ] You've read this runbook end-to-end before pasting any commands

**Estimated wall-clock time:** 90 minutes for WP-01 through WP-04.

## Decision: abort criteria

If WP-153-01 ping test fails (>50ms RTT or >1% packet loss to Whatbox NL netblock from your home Comcast IP), **DO NOT SIGN UP**. Whatbox-NL is then likely no improvement over seedit4me. Fall back to:
1. Bytesized Hosting (NL) — second choice
2. Seedhost.eu (NL) — third choice
Update D-17-MEDIA-master-plan.md Decisions log with the result and re-evaluate.

---

## WP-153-01 — Pre-signup ping/route verification (15 min)

### Step 1.1 — Find a Whatbox NL host to ping

Whatbox publishes NL server status pages. Pick a known hostname:

```bash
# Discover via DNS — Whatbox NL servers are typically nl-NN.whatbox.ca
# Try several candidate hostnames:
for h in nl-1.whatbox.ca nl-2.whatbox.ca nl-3.whatbox.ca; do
  echo "=== $h ==="
  dig +short "$h" 2>/dev/null
  echo ""
done

# Alternative: check Whatbox's status page at https://status.whatbox.ca
# for current server hostnames
```

If `dig` returns no results, fetch the current server list from:
- https://whatbox.ca/page/server-status (lists active servers)
- Whatbox knowledge base / signup page (shows current NL options)

Record the resolved IP(s) in your scratch notes — you'll use them for WP-01.2 and WP-01.3.

### Step 1.2 — RTT test

```bash
# Replace <whatbox-nl-ip> with IP from Step 1.1
WHATBOX_IP="<whatbox-nl-ip>"

echo "=== ICMP ping (50 packets) ==="
ping -c 50 "$WHATBOX_IP" | tail -3
# Look for: "X packets transmitted, Y received, Z% packet loss, time T"
# Look for: "rtt min/avg/max/mdev = A/B/C/D ms"
```

**PASS criteria:** avg RTT ≤ 50 ms AND packet loss ≤ 1%
**FAIL criteria:** avg RTT > 50 ms OR packet loss > 1% OR ping unreachable

If FAIL, abort signup. Try Bytesized next.

### Step 1.3 — Route inspection

```bash
echo "=== Traceroute (look for AS path quality) ==="
traceroute -n "$WHATBOX_IP" 2>&1 | head -20

# Look for:
# - Number of hops to reach (typical: 8-15 from US East coast)
# - Any hops with consistent timeout (* * *) — bad sign
# - Crosses one of: Telia, Hurricane Electric, Cogent, NTT, Level3 — good
# - Stays exclusively on Comcast → Hetzner — bad (was the seedit4me problem)
```

### Step 1.4 — Optional bandwidth probe (if Step 1.2 passed)

```bash
# Some Whatbox status pages publish public iperf3 endpoints; if not, skip.
# Or use a public Looking Glass to confirm route quality:
echo "=== Looking Glass ==="
echo "Visit https://lg.he.net/ — query the Whatbox IP from a US peer"
echo "Confirm path traverses AMS-IX"
```

### Step 1.5 — Record result + decision

Append to D-17-MEDIA-master-plan.md → Decisions log:

```
| 2026-MM-DD | WP-153-01 | Whatbox NL ping result: avg RTT N ms, loss N% | {PROCEED | ABORT} |
```

If PROCEED → continue to WP-153-02.
If ABORT → start over with Bytesized hostname (typically `bytesized.com` resolves to their NL pool).

---

## WP-153-02 — Whatbox NL signup + qBittorrent 5.2 selection (30 min)

### Step 2.1 — Signup

1. Go to https://whatbox.ca/plans
2. Select **NL location** (NOT NY/CA/IS)
3. Select 1TB or 2TB storage tier (1TB = $15/mo, 2TB = $25/mo — within budget; pick based on actual library + 30-day download buffer)
4. **At "Choose your client" step: SELECT qBittorrent**
   - DO NOT select rTorrent (the thing we're migrating away from)
   - DO NOT select Deluge (older, less actively maintained)
   - qBittorrent should show version 5.x or higher
5. Complete payment (annual prepay = ~10% discount; monthly = full flexibility)
6. Note your assigned hostname (e.g., `<youruser>.nl-N.whatbox.ca`) and credentials

### Step 2.2 — Initial WebUI login

```bash
# Whatbox provides qBit WebUI behind their auth + a per-user URL
# Typical pattern: https://<youruser>.whatbox.ca/qbittorrent/
# OR direct on a port: https://nl-N.whatbox.ca:NNNN/

# First-login checklist:
# 1. Change qBit WebUI password from default
# 2. Set qBit username (NOT same as Whatbox account username)
# 3. Enable 2FA if Whatbox offers (account-level, not per-app)
```

### Step 2.3 — Store credentials in Vault

**ON MAC MINI** (when reachable):
```bash
vault kv put secret/seedbox/whatbox \
  host=<your-host>.whatbox.ca \
  username=<whatbox-username> \
  password=<whatbox-password> \
  qbit_url=https://<your-host>.whatbox.ca/qbittorrent \
  qbit_user=<qbit-webui-username> \
  qbit_pass=<qbit-webui-password>

# Verify:
vault kv get -format=json secret/seedbox/whatbox | jq '.data.data | keys'
# Should output: ["host", "password", "qbit_pass", "qbit_url", "qbit_user", "username"]
```

### Step 2.4 — SSH key setup (replaces password auth)

```bash
# On your local Mac (Mac Mini OR MacBook — wherever you'll script from):
# Use existing key or generate dedicated:
ssh-keygen -t ed25519 -f ~/.ssh/whatbox_ed25519 -C "whatbox-$(date +%Y%m%d)" -N ""

# Add public key to Whatbox via their control panel:
# Whatbox dashboard → Account → SSH keys → Add new
# Paste contents of: cat ~/.ssh/whatbox_ed25519.pub

# Test SSH:
ssh -i ~/.ssh/whatbox_ed25519 <whatbox-username>@<your-host>.whatbox.ca 'hostname; uptime'
# Expected: hostname matches assigned server, uptime indicates server health
```

### Step 2.5 — IP allowlist (defense in depth)

```bash
# In Whatbox control panel:
# Security → IP allowlist → Add your home IP (find via: curl ifconfig.me)
# Optional: also allow Tailscale exit-node IPs if you'll access from elsewhere
```

---

## WP-153-03 — TRaSH-aligned categories on qBit (30 min)

### Step 3.1 — Verify qBit version

```bash
# Via qBit WebUI: top-right settings icon → About
# Confirm version 5.x. If 4.x, file ticket with Whatbox to upgrade.
```

### Step 3.2 — Configure default save path

In qBit WebUI: Tools → Options → Downloads:

```
Default save path: /home/<whatbox-username>/torrents/

Run external program on torrent finished: (leave empty for now)

Pre-allocate disk space: enabled (avoids fragmentation)
```

### Step 3.3 — Create TRaSH categories

In qBit WebUI: Categories panel (left sidebar) → Add new category for each:

| Category | Save path | Notes |
|---|---|---|
| `tv-sonarr` | `/home/<user>/torrents/tv/` | TRaSH TV path |
| `movies-radarr` | `/home/<user>/torrents/movies/` | TRaSH movies path |
| `music-lidarr` | `/home/<user>/torrents/music/` | TRaSH music path |
| `books-readarr` | `/home/<user>/torrents/books/` | TRaSH books path (placeholder for D-17-158) |

### Step 3.4 — Configure tags (optional but useful)

Tags for cross-cutting attributes:
- `1080p`, `2160p` (resolution)
- `cross-seed` (managed by cross-seed tool)
- `manual` (operator-added, not via arr)

### Step 3.5 — Verify directory creation

```bash
# Via SSH:
ssh -i ~/.ssh/whatbox_ed25519 <whatbox-username>@<your-host>.whatbox.ca \
  'ls -la torrents/'

# Expected: directories tv/, movies/, music/, books/ exist
# If not: create manually
ssh -i ~/.ssh/whatbox_ed25519 <whatbox-username>@<your-host>.whatbox.ca \
  'mkdir -p torrents/{tv,movies,music,books}'
```

---

## WP-153-04 — Throughput baseline test (15 min)

This is the gate before WP-153-05. If throughput is bad here, we know early — before reconfiguring any arr-app.

### Step 4.1 — Generate test file (100MB, on home Mac)

```bash
# On Mac Mini OR MacBook:
mkdir -p /tmp/whatbox-throughput-test
dd if=/dev/urandom of=/tmp/whatbox-throughput-test/test-100mb.bin bs=1m count=100
ls -lh /tmp/whatbox-throughput-test/test-100mb.bin
# Expected: 100M file
```

### Step 4.2 — Upload test (home → Whatbox)

```bash
echo "=== Upload test: home → Whatbox ==="
time scp -i ~/.ssh/whatbox_ed25519 \
  /tmp/whatbox-throughput-test/test-100mb.bin \
  <whatbox-username>@<your-host>.whatbox.ca:/tmp/

# Record: real time = X seconds
# Throughput = 100 MB / X seconds = Y MB/s
# Note: 100 Mbps = 12.5 MB/s, so Y MB/s × 8 = Mbps achieved
```

### Step 4.3 — Download test (Whatbox → home)

```bash
echo "=== Download test: Whatbox → home ==="
time scp -i ~/.ssh/whatbox_ed25519 \
  <whatbox-username>@<your-host>.whatbox.ca:/tmp/test-100mb.bin \
  /tmp/whatbox-throughput-test/test-100mb-back.bin

# Record: real time = X seconds
# Throughput = 100 MB / X = Y MB/s
# Multiply by 8 for Mbps
```

### Step 4.4 — Cleanup test files

```bash
# On Whatbox:
ssh -i ~/.ssh/whatbox_ed25519 <whatbox-username>@<your-host>.whatbox.ca \
  'rm /tmp/test-100mb.bin'

# On home:
rm -rf /tmp/whatbox-throughput-test/
```

### Step 4.5 — Record + decision

Append to D-17-MEDIA-master-plan.md → Decisions log:

```
| 2026-MM-DD | WP-153-04 | Throughput: upload N Mbps, download N Mbps | {PROCEED | INVESTIGATE} |
```

**PROCEED criteria:** download ≥ 50 Mbps sustained
**INVESTIGATE criteria:** download < 50 Mbps — likely needs Mullvad-on-QNAP fallback (D-17-154 WP-05)

If PROCEED → continue to WP-153-05 (next session, not part of this 90-min block).
If INVESTIGATE → STOP. Open D-17-154 and run the Mullvad-on-QNAP track before reconfiguring arr-apps.

---

## Rollback per phase

| At end of WP | If you abort here, the cost is | Action to revert |
|---|---|---|
| WP-153-01 (ping fail) | Time only, no signup | Try Bytesized; D-17-153 stays NOT STARTED |
| WP-153-02 (signup done, qBit not configured) | $15 (1 month minimum) | Cancel Whatbox; D-17-153 stays NOT STARTED |
| WP-153-03 (categories configured) | $15 + 1 hr | Cancel Whatbox; no arr-app reconfiguration done yet |
| WP-153-04 (throughput tested) | $15 + 90 min | Cancel Whatbox if results bad; nothing else reconfigured |

**Critical:** WP-153-01 through WP-153-04 do NOT touch any arr-app configuration. Aborting at any of these phases leaves your current seedit4me + rTorrent + Sonarr/Radarr/Lidarr setup completely intact. Zero blast radius until WP-153-05.

---

## WP-153-05 — Prowlarr API reconfiguration (Whatbox qBit, parallel mode)

This is the point where Whatbox becomes active in your media acquisition pipeline. Seedit4me stays alive; we're adding Whatbox as a secondary for testing.

### Step 5.1 — Update Prowlarr download client

**On QNAP (or via Tailscale from home):**

1. Open Prowlarr web UI (usually http://qnap-ip:9696)
2. Settings → Download Clients
3. Click the existing **seedit4me-rtorrent** entry to edit it
   - **Disable** it for now (toggle off, don't delete)
   - This stops new searches from going to seedit4me
4. Click **"Add Download Client"** → **qBittorrent**
   - **Name:** `whatbox-qbit-pilot` (reflects this is testing)
   - **Host:** `<your-host>.whatbox.ca` (from WP-02)
   - **Port:** `6881` (or check Whatbox control panel for their qBit API port; typical is default or custom)
   - **Username:** `<qbit-webui-username>` (from WP-02.3 Vault entry)
   - **Password:** `<qbit-webui-password>` (from Vault)
   - **Use SSL:** **enabled** (Whatbox uses HTTPS for API)
   - **URL Base:** `/` (Whatbox qBit typically at root)
   - Test connection (Prowlarr will verify API reachability)
5. **Priority:** Set **seedit4me-rtorrent** to priority 2, **whatbox-qbit-pilot** to priority 1
   - Prowlarr will now send NEW searches to Whatbox qBit first
6. Save

### Step 5.2 — Verify Prowlarr sends traffic to Whatbox

```bash
# In Prowlarr web UI: Settings → Health → Job History
# Trigger a manual search on an indexer (e.g., search for a trending show)
# Check Prowlarr logs for "sending to whatbox-qbit-pilot"
# OR: check Whatbox qBit WebUI: Activity tab should show new torrent (if found + grabbed)
```

### Step 5.3 — Record decision

Append to D-17-MEDIA-master-plan.md Decisions log:

```
| 2026-MM-DD | WP-153-05 | Prowlarr reconfigured; Whatbox qBit API reachable; seedit4me disabled | PROCEED |
```

**Acceptance criteria:**
- [ ] Prowlarr can reach Whatbox qBit API
- [ ] At least one torrent successfully grabbed and added to Whatbox qBit (verify in WebUI)
- [ ] seedit4me-rtorrent disabled in Prowlarr (no longer receiving searches)

**Rollback:**
```bash
# In Prowlarr: re-enable seedit4me-rtorrent, disable whatbox-qbit-pilot
# In Whatbox: manually delete test torrents (qBit WebUI)
# No arr-app changes yet, so zero impact
```

**Estimated time:** 30 min (including first grab verification)

---

## WP-153-06 — Sonarr + Radarr + Lidarr: add Whatbox qBit as secondary client

Now that Prowlarr sends torrents to Whatbox, the arr-apps need to know about the Whatbox download client for import post-processing. We add it without making it primary yet.

### Step 6.1 — Sonarr download client (secondary)

**On QNAP (http://qnap-ip:8989):**

1. Settings → Download Clients
2. Click existing **seedit4me-rtorrent** to verify it's still there (priority 2 or lower)
3. Add new client: **qBittorrent**
   - **Name:** `whatbox-qbit-pilot`
   - **Host:** `<your-host>.whatbox.ca`
   - **Port:** `6881` (match Prowlarr)
   - **Username/Password:** (from Vault)
   - **Use SSL:** enabled
   - **URL Base:** `/`
   - Test connection
4. **Priority:** Set Whatbox to priority 1, seedit4me to priority 2
   - This means Sonarr will check Whatbox qBit for completed downloads first
5. Save

### Step 6.2 — Radarr download client (secondary)

Repeat Step 6.1 for Radarr (http://qnap-ip:7878):
- Same configuration
- Same priorities

### Step 6.3 — Lidarr download client (secondary)

Repeat for Lidarr (http://qnap-ip:8686):
- Same configuration
- Same priorities

### Step 6.4 — Verify arr-apps see Whatbox qBit

```bash
# On QNAP, check each arr-app logs for "Download client: whatbox-qbit-pilot"
# Or in Sonarr/Radarr/Lidarr UI → Health → should show no warnings about Whatbox reachability

# Try a manual search + grab in Sonarr (search for a TV episode, let Prowlarr/Whatbox grab it)
# Wait 5 min, check if Sonarr auto-imports it:
# If yes: Whatbox client is working
# If no: check logs for import path issues
```

**Acceptance criteria:**
- [ ] Whatbox qBit client appears in all three arr-apps (Sonarr, Radarr, Lidarr)
- [ ] No connection errors in health/logs
- [ ] Whatbox priority is higher than seedit4me (will be checked first for imports)

**Rollback:**
```bash
# Delete whatbox-qbit-pilot from Sonarr, Radarr, Lidarr
# No configuration changes yet, so imports will continue from seedit4me
```

**Estimated time:** 30 min (3 × 10 min each)

---

## WP-153-07 — Lidarr pilot: add 1 album (smallest blast radius)

**Goal:** Add a single album via Whatbox → verify download → verify import → verify hardlink → verify Navidrome serves it.

This is the lowest-risk test. If Lidarr's import path or hardlink setup breaks, it only affects one album.

### Step 7.1 — Choose a test album

Pick something small (< 500 MB) and widely available:
- Example: "The Dark Side of the Moon" by Pink Floyd
- Or any album you actually want to add
- Search in Lidarr: Artists → Add new → search

### Step 7.2 — Add artist to Lidarr

1. Lidarr web UI (http://qnap-ip:8686)
2. Artists → Add new
3. Search for artist name (e.g., "Pink Floyd")
4. Select artist
5. Root folder: `/data/media/music/` (matches TRaSH path from WP-03)
6. Quality Profile: (use default or existing)
7. Add

### Step 7.3 — Search for specific album

1. Click artist → Albums
2. Find test album
3. Click "Add" or "Download"
4. Prowlarr searches → Whatbox qBit grabs torrent

### Step 7.4 — Monitor download + import

```bash
# Watch Whatbox qBit WebUI: Downloads tab
# Verify torrent appears, shows as downloading, completes within 5 min

# Switch to Lidarr: Activities → History
# After qBit completes, Lidarr should auto-import (look for "Album imported")
# If import fails: check logs for error (path issue, file format, metadata)
```

### Step 7.5 — Verify hardlink + Navidrome

```bash
# On QNAP, check hardlinks:
ls -li /data/media/music/<artist>/<album>/*.flac | head -3
# Output should show same inode across files (hardlink indicator)

# Test Navidrome playback:
# Open Navidrome web UI (http://qnap-ip:4533)
# Search for album → click → play track
# Verify 30 seconds of uninterrupted playback
```

### Step 7.6 — Record result

```
| 2026-MM-DD | WP-153-07 | Lidarr pilot: 1 album added via Whatbox → imported → hardlinked → served by Navidrome | PASS |
```

**Acceptance criteria (all must pass to proceed to WP-08):**
- [ ] Torrent downloaded to Whatbox qBit within 5 min
- [ ] Lidarr auto-imported without errors
- [ ] Files hardlinked (same inode in torrents/ and media/)
- [ ] Navidrome serves playback without errors
- [ ] No orphaned files in import staging

**Rollback:**
```bash
# Remove artist from Lidarr (triggers file deletion)
rm -rf /data/media/music/<artist>
rm -rf /data/torrents/music/<artist>  # Clean up torrent copy if needed
# On Whatbox qBit: delete torrent
```

**Estimated time:** 1 hr (including download + import verification)

---

## WP-153-08 — Sonarr pilot: add 1 episode (same pattern)

Repeat WP-07 for Sonarr:

### Step 8.1 — Choose test show

Pick a show with small episodes (< 1 GB per episode):
- Example: a recent animated series or documentary
- Something you'd actually watch

### Step 8.2 — Add series to Sonarr

1. Sonarr web UI (http://qnap-ip:8989)
2. Series → Add new
3. Search show name
4. Root folder: `/data/media/tv/` (TRaSH path from WP-03)
5. Season monitoring: monitor only the latest season (or first episode)
6. Add

### Step 8.3 — Search + grab

1. Click series → Seasons
2. Find test episode (recent = likely available)
3. Click "download" or "search now"
4. Prowlarr searches → Whatbox qBit grabs

### Step 8.4 — Monitor + verify

```bash
# Whatbox qBit: verify torrent completes
# Sonarr Activity → History: watch for "Episode imported"
# Check hardlinks: ls -li /data/torrents/tv/<show>/ | head -3
# Verify Plex/Jellyfin plays (or manual VLC test from QNAP)
```

### Step 8.5 — Record result

```
| 2026-MM-DD | WP-153-08 | Sonarr pilot: 1 episode added via Whatbox → imported → hardlinked | PASS |
```

**Acceptance criteria (all must pass):**
- [ ] Episode downloaded to Whatbox qBit
- [ ] Sonarr auto-imported without errors
- [ ] Files hardlinked to media/
- [ ] Playback verified (not just Plex metadata)

**Rollback:** Delete series from Sonarr (removes files)

**Estimated time:** 1 hr

---

## WP-153-09 — Radarr pilot: add 1 movie (same pattern)

Repeat for Radarr:

### Step 9.1 — Choose test movie

Small file (< 4 GB):
- Example: a 720p indie film or old movie
- Something actually worth watching

### Step 9.2 — Add movie to Radarr

1. Radarr web UI (http://qnap-ip:7878)
2. Movies → Add new
3. Search movie title
4. Root folder: `/data/media/movies/` (TRaSH path)
5. Add

### Step 9.3 — Search + grab

Click movie → "Search movie" → Prowlarr grabs from Whatbox

### Step 9.4 — Monitor + verify

Same as WP-07/08:
- Whatbox downloads
- Radarr imports
- Hardlinks verified
- Playback tested

### Step 9.5 — Record result

```
| 2026-MM-DD | WP-153-09 | Radarr pilot: 1 movie added via Whatbox → imported → hardlinked | PASS |
```

**Acceptance criteria:**
- [ ] Download, import, hardlink, playback all pass
- [ ] No import failures despite different file format (mkv vs flac)

**Rollback:** Delete movie from Radarr

**Estimated time:** 1 hr

---

## WP-153-10 — Promote Whatbox qBit to primary across all arr-apps

All three pilots (Lidarr, Sonarr, Radarr) have passed. Time to make Whatbox the default for NEW downloads.

### Step 10.1 — Update all arr-apps

In Sonarr, Radarr, Lidarr:

**Settings → Download Clients:**
- Move **whatbox-qbit-pilot** to priority 1
- Move **seedit4me-rtorrent** to priority 2 (becomes fallback only)

### Step 10.2 — Verify in Prowlarr

Prowlarr should still have Whatbox at priority 1 (from WP-05). Confirm:

**Settings → Download Clients:**
- whatbox-qbit-pilot: priority 1
- seedit4me-rtorrent: priority 2 (disabled)

### Step 10.3 — Add one fresh torrent to each arr-app

Test that NEW searches now go to Whatbox:
- Sonarr: search for upcoming episode
- Radarr: search for new movie release
- Lidarr: search for new album

Verify all land in Whatbox qBit, not seedit4me.

### Step 10.4 — Record

```
| 2026-MM-DD | WP-153-10 | Whatbox qBit promoted to primary; seedit4me demoted to fallback | PROCEED |
```

**Acceptance criteria:**
- [ ] All three arr-apps have Whatbox at priority 1
- [ ] Manual searches land in Whatbox qBit
- [ ] seedit4me remains as fallback (disabled in Prowlarr, but still active in arr-apps for legacy downloads)

**Rollback:**
```bash
# Swap priorities back: seedit4me priority 1, Whatbox priority 2
# Manual searches will resume going to seedit4me
```

**Estimated time:** 15 min

---

## WP-153-11 — 30-day parallel run (passive monitoring)

From this point forward, all NEW torrents go to Whatbox qBit. Old torrents on seedit4me continue seeding for ratio/community good.

### Monitoring schedule:

**Daily (5 min):**
- Check Whatbox qBit WebUI: active torrents < expected queue length?
- Check QNAP Syncthing: any large sync backlogs?

**Weekly (15 min at day 7, 14, 21, 28):**
- Whatbox qBit: check for failed torrents (if any, manually remove)
- Seedit4me rTorrent: note number of active torrents (should be slowly declining)
- Syncthing: verify sync completes within expected window

**Gate at day 30:** Proceed to WP-12 (cancel seedit4me) only if:
- [ ] ≥3 complete downloads via Whatbox (Lidarr, Sonarr, Radarr all working)
- [ ] Sync throughput sustained ≥50 Mbps
- [ ] No corruption or import failures in last 7 days
- [ ] Seedit4me ratio acceptable (or you've decided to cut it)

**Estimated time:** 30 days passive + 1 min daily checks

---

## WP-153-12 — End parallel run: cancel seedit4me

After day 30 gate passes:

### Step 12.1 — Verify seedit4me is no longer needed

```bash
# Check current active torrents on seedit4me rTorrent
# Via web UI: note how many are still seeding
# If < 10 active, safe to cancel
# If > 10 and ratio not important: cancel anyway (your new standard is Whatbox ratio)
```

### Step 12.2 — Cancel seedit4me subscription

1. Log into seedit4me account (online portal)
2. Go to Billing → Subscriptions
3. Cancel subscription (usually effective end of current billing cycle)
4. Download final rTorrent config as backup (optional, for record-keeping)

### Step 12.3 — Clean up local references

```bash
# On QNAP:
# Remove seedit4me-rtorrent from Sonarr/Radarr/Lidarr (no longer needed)
# Or leave disabled as emergency fallback

# On home Mac:
# Remove seedit4me SSH keys (~/.ssh/seedit4me_*)
# Remove Vault entry: vault kv delete secret/seedbox/seedit4me
```

### Step 12.4 — Record

```
| 2026-MM-DD | WP-153-12 | Seedit4me subscription cancelled; all production downloads now via Whatbox | DONE |
```

**Acceptance criteria:**
- [ ] Seedit4me subscription terminated
- [ ] No active torrents remain on seedit4me (or acceptable to abandon seeding)
- [ ] All arr-apps default to Whatbox qBit
- [ ] No regression in download speed or import quality

**Estimated time:** 15 min (mostly waiting for cancellation to process)

---

## WP-153-13 — Final documentation + decision log

### Step 13.1 — Summarize in master plan

Add final entry to D-17-MEDIA-master-plan.md Decisions log:

```
| 2026-MM-DD | WP-153-01 through WP-153-12 | Seedbox migration complete: seedit4me → Whatbox NL + qBittorrent | DECISION CLOSED |
```

### Step 13.2 — Document lessons learned

Edit this runbook (seedbox-migration-d-17-153.md):
- Add "Lessons learned" section at end
- Note any surprises (e.g., "hardlinks worked perfectly with qBit", or "Syncthing had one hiccup on day 14")
- Note any workarounds applied (if any)

### Step 13.3 — Commit final state

```bash
cd ~/repos/integrated-ai-platform
git add docs/decision-records/D-17-MEDIA-master-plan.md \
        docs/runbooks/seedbox-migration-d-17-153.md
git commit -m "docs(D-17-153): Seedbox migration to Whatbox NL complete; all pilots passed; 30-day parallel done"
git log --oneline -n 1
```

### Step 13.4 — Close D-17-153

In D-17-MEDIA-master-plan.md, update the tracker row:

```
| D-17-153 | Seedbox migration (Whatbox NL + qBittorrent) | P1 | DONE | none | 2-4 hr active + 30 days parallel | 2026-MM-DD | 2026-MM-DD |
```

**Estimated time:** 30 min (documentation + commit)

---

## Rollback summary (across all phases)

| Phase | If aborting here, revert | Cost | Notes |
|---|---|---|---|
| WP-05 (Prowlarr config) | Disable Whatbox client in Prowlarr; re-enable seedit4me | 5 min | Zero impact; Whatbox exists but unused |
| WP-06 (arr-app clients) | Delete Whatbox client from Sonarr/Radarr/Lidarr | 10 min | Imports resume from seedit4me |
| WP-07/08/09 (pilots) | Delete test artist/series/movie from arr-apps | 15 min | Files deleted; Whatbox torrent deleted manually |
| WP-10 (promote primary) | Swap priorities back: seedit4me → 1, Whatbox → 2 | 10 min | New downloads resume on seedit4me |
| WP-11/12 (parallel + cancel) | After day 30 gate, if something breaks, keep seedit4me running longer (max 90 days is typical) | Extends monthly cost | Fallback is always available |

---

## After this block — what's next

After WP-153-12 COMPLETE, D-17-153 is **DONE**. Unblock:
- D-17-154 (Syncthing hardening) — can start immediately
- D-17-155 (TRaSH path migration) — can start immediately

Update master plan tracker before closing the session:

```bash
cd ~/repos/integrated-ai-platform
# Edit docs/decision-records/D-17-MEDIA-master-plan.md
# Update D-17-153 status to DONE
# Update D-17-154, D-17-155 status to NOT BLOCKED (can start anytime)
# Add commit on travel branch:
git add docs/decision-records/D-17-MEDIA-master-plan.md
git commit -m "docs(D-17-153): WP-05 through WP-13 documented (paste-ready); all migration runbook complete"
```

---
