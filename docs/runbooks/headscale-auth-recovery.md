# Headscale Auth Recovery Runbook

**Purpose:** Disaster recovery procedures for re-establishing Tailscale/Headscale auth when Headscale server (Mac Mini) is asleep, network-unreachable, or destroyed while operator is traveling.

**Trigger:** Use this runbook when:
- Mac Mini is down/asleep and Tailscale auth fails on traveling device (MacBook, iPad, phone)
- Headscale Docker container is inaccessible and you can't reach the control plane
- You have no access to home network LAN and can't wake Mac Mini remotely
- Emergency pre-auth keys are needed to re-auth without Mac Mini

**Time estimate:** 15–30 min (depending on scenario)

---

## Part 1: Prevention (do NOW while Mac Mini is reachable)

### 1.1 Generate emergency pre-auth keys

Emergency pre-auth keys allow re-auth to Headscale even when the server is temporarily inaccessible. Generate them now and store securely.

**On Mac Mini (when reachable):**

```bash
# SSH into Mac Mini
ssh adrian@192.168.10.145
# or via Tailscale if already auth'd
ssh adrian@100.64.0.1

# Enter Headscale container shell
docker exec -it headscale headscale preauthkeys list

# Generate 3 emergency pre-auth keys (one active, one backup, one rotation buffer)
docker exec -it headscale headscale preauthkeys create \
  --expiration=2027-05-07 \
  --reusable=false \
  --description="Emergency key 1 — iPad/traveling use"

docker exec -it headscale headscale preauthkeys create \
  --expiration=2027-05-07 \
  --reusable=false \
  --description="Emergency key 2 — backup"

docker exec -it headscale headscale preauthkeys create \
  --expiration=2027-05-07 \
  --reusable=false \
  --description="Emergency key 3 — rotation buffer"

# List all keys to see the generated ones
docker exec -it headscale headscale preauthkeys list
```

Record the full key strings (they look like: `~key-1234567890abcdef...`).

### 1.2 Document Headscale configuration

**On Mac Mini:**

```bash
# Get Headscale server_url and base_domain
docker exec headscale cat /etc/headscale/config.yaml | grep -A5 "server_url\|base_domain"

# Example output:
# server_url: https://headscale.local.home:8443
# or
# server_url: https://headscale.home.arpa:443
# (adjust to YOUR actual Headscale URL)

# Get Headscale Docker container ID for restart/recovery
docker ps | grep headscale
```

Note: Headscale URL is typically one of:
- `https://<mac-mini-hostname>.local.home:<port>`
- `https://<mac-mini-tailscale-ip>:8443` (if accessing via Tailscale IP 100.64.x.x)
- `https://headscale.home.arpa:443` (depends on your setup)

### 1.3 Store emergency credentials securely

**Store in THREE places:**

**Location 1: Vaultwarden** (encrypted, syncable)
- Entry title: "Headscale Emergency Auth Keys"
- Fields:
  - Headscale URL: `https://headscale.local.home:8443` (adjust to YOUR URL)
  - Key 1 (active): `~key-...`
  - Key 2 (backup): `~key-...`
  - Key 3 (rotation): `~key-...`
  - Expiration: 2027-05-07
  - Notes: "Use only when Mac Mini unreachable; rotate quarterly"

**Location 2: Offline encrypted file**
- Store in 1Password or Strongbox (offline-accessible)
- Filename: `headscale-emergency-keys.txt.gpg` or similar
- Encrypt with your usual GPG key or 1Password vault key
- Content: same as Vaultwarden entry (plain text, then encrypted)
- Keep on MacBook offline storage, iPad home screen, phone

**Location 3: Printed paper backup**
- Print Vaultwarden entry on paper
- Store in fireproof location (home safe, safe deposit box, parent's house)
- Refresh every 6 months (when rotating keys)

---

## Part 2: Recovery procedures (choose by scenario)

### Scenario A: Mac Mini asleep but reachable on LAN

**Use this if:** You're at home or nearby, Mac Mini is on the same LAN but asleep.

**Recovery steps:**

```bash
# Step 1: Wake Mac Mini via LAN
# Option A1: SSH wake-on-LAN (if configured)
wakeonlan 00:11:22:33:44:55  # Replace with Mac Mini MAC address

# Option A2: SSH to Mac Mini (may wake it if SSH is enabled)
ssh adrian@192.168.10.145

# Step 2: If SSH succeeds, Headscale should be reachable. Re-auth MacBook:
tailscale up --login-server=https://192.168.10.145:8443

# Step 3: Verify auth succeeded
tailscale status
# Should show: your-macbook is "Idle" with peers listed

# Done. Mac Mini is now reachable and auth is refreshed.
```

**Verification:**
```bash
tailscale status | grep -E "100.64.0|DERP"
# Should show Mac Mini with an IP like "100.64.0.1" and connectivity status "DERP" or direct
```

**Rollback if fails:**
- If SSH times out: Mac Mini may be off, not just asleep. Proceed to Scenario B.
- If tailscale up fails: Mac Mini is reachable but Headscale container may be crashed. SSH in and check `docker ps`.

---

### Scenario B: Mac Mini at home but network unreachable from outside

**Use this if:** You're at home, Mac Mini is reachable via LAN or console, but Headscale is down or container is crashed.

**Recovery steps:**

```bash
# Step 1: SSH to Mac Mini via LAN IP
ssh adrian@192.168.10.145

# Step 2: Check Headscale container status
docker ps | grep headscale
# If container is NOT running, start it:
docker start headscale

# Wait 10 seconds for container to initialize
sleep 10

# Step 3: Verify Headscale is responding
curl -k https://192.168.10.145:8443  # Ignore SSL cert errors with -k
# Should return HTML (Headscale web UI) or JSON

# Step 4: Re-auth MacBook via Headscale
tailscale up --login-server=https://192.168.10.145:8443

# Step 5: Verify
tailscale status
```

**If Docker container is corrupt:**
```bash
# Check container logs
docker logs headscale

# If logs show errors, try container restart
docker restart headscale
docker logs headscale  # Check if it stabilized

# If restart fails, escalate to full Headscale Docker rebuild (beyond this runbook)
```

**Rollback:**
- If Headscale won't start: this runbook can't recover; you'll need to redeploy Headscale (D-17-151 or equivalent).
- Fallback: Use emergency pre-auth key with a public Headscale instance as temporary gateway (not recommended; covered in D-17-150).

---

### Scenario C: Mac Mini unreachable and operator traveling (no LAN access)

**Use this if:** You're away from home, can't reach Mac Mini LAN, Headscale is inaccessible, and you need to re-auth your MacBook/iPad/phone.

**Recovery steps:**

**Option C1: Use emergency pre-auth key to re-establish auth (RECOMMENDED)**

```bash
# Step 1: Retrieve emergency pre-auth key from offline backup
# From your phone/iPad: open Strongbox or 1Password
# Retrieve the "Headscale Emergency Auth Keys" entry
# Copy the Headscale URL and one pre-auth key

# Step 2: On MacBook, log out of current Tailscale state
tailscale logout

# Step 3: Re-auth using emergency key and Headscale URL
# Replace <headscale-url> and <emergency-key> with values from Step 1
tailscale up --login-server=https://headscale.local.home:8443 \
  --auth-key=~key-1234567890abcdef...

# Step 4: Verify re-auth succeeded
tailscale status

# You should now see Tailscale peers. Connection will show as "DERP" (relay)
# since Mac Mini is down. Direct connection resumes when Mac Mini comes back online.
```

**What just happened:**
- Headscale maintains a list of authorized users and devices locally (in its database on Mac Mini).
- Even though Mac Mini is currently unreachable, Headscale *has already issued* you a node certificate.
- Your device's Tailscale daemon now has that certificate cached in `~/.local/share/tailscale/certs/`.
- You can communicate with **other authorized Tailscale peers** (iPad, phone at home, etc.) via DERP relay.
- When Mac Mini comes back online, direct LAN connections resume.

**Option C2: Use Tailscale Inc. public control plane as temporary fallback (NOT RECOMMENDED)**

If emergency pre-auth keys are exhausted or lost:

```bash
# Fallback: re-auth to standard Tailscale Inc. control plane
tailscale logout
tailscale up

# Browser window opens; log in with your adbcox@gmail.com Tailscale Inc. account
# You'll be in a separate (empty) Tailscale Inc. tailnet, isolated from home Headscale

# Once Mac Mini is back online, re-auth back to Headscale:
tailscale logout
tailscale up --login-server=https://headscale.local.home:8443 \
  --auth-key=~key-<fresh-key>

# This restores home connectivity.
```

**⚠️ WARNING:** Option C2 breaks doctrine (Proton + self-hosted Headscale only; no Tailscale Inc. except travel auth bridge). Use only if emergency keys fail and no alternative exists.

**Rollback/verification:**
```bash
# Check which control plane you're on
tailscale status | head
# Output should show Tailscale Inc. login server if C2 was used

# Verify peer list
tailscale status | grep -E "100\.(64|127)\." 
# Headscale IPs are in 100.64.0.0/10 range
```

---

## Part 3: Periodic key rotation (quarterly)

**Quarterly maintenance:** Rotate emergency pre-auth keys to expire old ones and refresh backups.

```bash
# When: Every 3 months, or when operator leaves home for >7 days

# Step 1: On Mac Mini (when reachable), revoke expired keys
ssh adrian@192.168.10.145
docker exec -it headscale headscale preauthkeys list
# Identify expired or soon-expiring keys

docker exec -it headscale headscale preauthkeys delete <key-id>
# <key-id> is the short identifier shown in list output

# Step 2: Generate 3 new keys with new expiration
docker exec -it headscale headscale preauthkeys create \
  --expiration=2027-08-07 \
  --reusable=false \
  --description="Emergency key 1 — Q3 2026"

# (repeat 2 more times with different descriptions)

# Step 3: Update offline storage
# Edit 1Password / Strongbox entry
# Update Vaultwarden entry
# Print and update paper backup

# Step 4: Destroy old paper printouts (shred or burn)
```

---

## Part 4: Emergency pre-auth key count (operator decision)

**Decided (2026-05-07):** Maintain 3 emergency pre-auth keys at any time.

**Allocation:**
- Key 1: "Active" — primary emergency key for crisis recovery. Single-use (expires after consumption).
- Key 2: "Backup" — secondary key, identical validity to Key 1. Stored in secondary offline location (1Password).
- Key 3: "Rotation buffer" — held fresh for next quarterly rotation. Not consumed except during rotation cycle.

**Rationale:**
- One consumed during recovery (Key 1)
- One fresh after consumption (Key 2)
- One buffer for next scheduled rotation (Key 3) without gap
- Below 3: risk getting caught between rotations if traveling during key refresh
- Above 3: added management surface without recovery benefit

**Quarterly rotation reminder:** When rotating keys, revoke all 3 old keys and generate 3 new ones. Zero-day gap risk = zero.

---

## Part 5: Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `tailscale up` hangs or times out | Headscale unreachable, network latency | Verify Headscale URL is correct; check Mac Mini is online; retry with `--timeout=10s` |
| `Cannot authenticate; invalid auth key` | Pre-auth key expired or revoked | Generate fresh key on Mac Mini; update offline storage |
| `Authentication succeeded but no peers visible` | Headscale auth succeeded but peer list empty | Normal when Mac Mini offline. Wait for Mac Mini to come online; `tailscale status` will populate. |
| `DERP relay only; no direct connection` | Mac Mini down, Tailscale using relay | Once Mac Mini is reachable, `tailscale up` again to refresh direct connection. |
| `tailscale status shows two different control planes` | Both Tailscale Inc. and Headscale clients active | See D-17-150 (client consolidation). Log out of unwanted control plane. |

---

## Appendix: Headscale Docker reference

**Container location:** Mac Mini, Docker on local machine

**Typical docker-compose.yml snippet:**
```yaml
headscale:
  image: headscale/headscale:latest
  container_name: headscale
  ports:
    - "8443:8443"  # HTTPS web UI
    - "3478:3478/udp"  # STUN
  volumes:
    - /var/lib/headscale/config:/etc/headscale
    - /var/lib/headscale/data:/var/lib/headscale
  environment:
    - TZ=UTC
```

**Restart Headscale container:**
```bash
docker restart headscale
docker logs headscale  # Verify it started
```

**Check if container is running:**
```bash
docker ps | grep headscale
# If not listed, container is stopped
docker start headscale
```

---

## Appendix: Tailscale CLI reference

**Check current control plane:**
```bash
tailscale status | head -3
# Shows which server you're authenticated to
```

**Switch control planes:**
```bash
# Logout of current
tailscale logout

# Re-auth to Headscale (self-hosted)
tailscale up --login-server=https://headscale.local.home:8443

# Or re-auth to Tailscale Inc. (public)
tailscale up
```

**View all connected peers:**
```bash
tailscale status
```

**Force reconnect:**
```bash
tailscale down
tailscale up
```

---

## Related documents

- **D-17-150:** Tailscale client consolidation decision (brew CLI vs Tailscale.app)
- **D-17-MEDIA master plan:** Overall media stack dependencies on Headscale
- **Master log §3:** Headscale architecture, current config values
- **Vaultwarden admin:** Managing encrypted secrets (Headscale URLs, keys)

---

**Last updated:** 2026-05-07 (flight session)  
**Reviewed by:** Adrian Cox  
**Status:** DESIGN COMPLETE (operator decided emergency key count = 3; WP-145-01 ready for execution when home)
