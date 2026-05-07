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

## After this block — what's next

After WP-153-04 PASSes, the next session is WP-153-05 (Prowlarr → Whatbox qBit API connection). That's 30 min and starts the actual migration. You can pause for days/weeks between blocks safely.

Update master plan tracker before closing the session:

```bash
cd ~/repos/integrated-ai-platform
# Edit docs/decision-records/D-17-MEDIA-master-plan.md
# Update WP-153-01 through WP-153-04 status to DONE
# Add commit on travel branch:
git add docs/decision-records/D-17-MEDIA-master-plan.md
git commit -m "docs(D-17-153): WP-01 through WP-04 complete; throughput X Mbps; PROCEED"
```

---
