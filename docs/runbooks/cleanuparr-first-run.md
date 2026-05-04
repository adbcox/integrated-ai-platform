# Cleanuparr first-run — UI wizard + Seeker enablement

**Status:** Active. Authored 2026-05-04 (D-17-49 closure progression).
**Deliverable:** D-17-49 (Cleanuparr Seeker-consolidated deployment).
**Smoke evidence:** `docs/phase-18/d-17-49/SMOKE.md`.
**Companion deliverable:** D-17-76 (`secret/seedbox/qbittorrent` bootstrap — Cleaner-module-only gate).

This runbook walks the operator through Cleanuparr's first-run setup: UI
wizard completion (Section 1) followed by Seeker module enablement
(Section 2). Both are operator-UI actions; nothing here is a Claude/repo
action.

**Scope:**
- In scope: wizard, Seeker (missing/upgrade hunts via Sonarr/Radarr APIs).
- Out of scope: Queue Cleaner + Download Cleaner enablement. Those are
  blocked on `secret/seedbox/qbittorrent` (D-17-76 commit-2) and tracked
  for a later operator session — see "Cleaner modules — deferred" at the
  bottom of this runbook.

## Pre-flight checks (no action required if all green)

Run from the Mac Mini control plane:

```bash
# 1. Container is up + healthy
docker ps --format '{{.Names}} {{.Status}}' | grep cleanuparr

# 2. Sonarr + Radarr API keys are rendered for the cleanuparr sidecar
ls -la /Users/admin/.vault-agent-secrets/cleanuparr/credentials.env
# expect: file present, mode 0440

# 3. Wizard not yet completed (the reason you're here)
curl -sS http://localhost:11011/api/v1/health
# expect: {"error":"Setup required"}

# 4. UI route resolves via Caddy + Dnsmasq
# (run from a workstation on the LAN — Mac Mini's local resolver does
#  NOT honor Dnsmasq for shell traffic; that's expected)
```

If (1) is not "Up (healthy)" or (2) shows the file missing: stop. The
sidecar didn't render. Investigate before proceeding — do not run the
wizard against a broken auth posture.

## Section 1 — UI wizard

### Step 1.1 — open the UI

Two routes work:

- **Preferred:** `https://cleanuparr.internal/` from a LAN workstation.
  Caddy fronts the route at `docker/caddy/Caddyfile:149`; Dnsmasq host
  entry on OPNsense maps `cleanuparr.internal → 192.168.10.145`.
- **Fallback (Mac Mini console only):** `http://localhost:11011/`.
  Use this if the Caddy/Dnsmasq path is broken. Plain HTTP — fine for
  loopback only, do not expose externally.

### Step 1.2 — complete the wizard

Cleanuparr's first-run wizard sets up local app posture (admin auth, DB
init). It does NOT require download-client credentials at this stage —
that's the D-17-76 / Cleaner-module gate, not a Section 1 concern.

When prompted:

- **Admin user / password:** create local credentials. **Record them
  in your password manager** (1Password / vault — your choice). The
  platform Vault is not the storage target for app-local UI auth; treat
  these like Sonarr/Radarr admin credentials (operator-managed,
  operator-stored). API keys created later in the UI ARE Vault-tracked
  (see Step 2.4), but the wizard's user/password is not.
- **Application URL / external URL:** enter `https://cleanuparr.internal`.
  This must match the Caddy front used by other arr-stack peers — F6
  doctrine: URL values are part of the credential, not metadata.
  Mismatch here causes the same class of drift D-17-38 caught in
  Sonarr/Radarr/Prowlarr.
- **Storage paths (if asked):** leave defaults. Container has
  `/config` (named volume `cleanuparr-config`), `/downloads` (QNAP
  bind), and `/data` (QNAP bind) already mounted per
  `~/control-center-stack/stacks/arr-stack/docker-compose.yml:330-333`.

### Step 1.3 — verify wizard completion

```bash
curl -sS http://localhost:11011/api/v1/health
# expect: 200 with non-error body — NOT {"error":"Setup required"}
```

If the response is still `Setup required`, the wizard didn't persist.
Check container logs (`docker logs cleanuparr --tail 50`) and re-run the
wizard.

## Section 2 — Seeker enablement

Seeker hunts for missing media and upgrades via the Sonarr/Radarr APIs.
It does NOT talk to download clients, so it has everything it needs once
Section 1 is done. Conservative caps are already staged per
`docs/phase-18/d-17-49/SMOKE.md` lines 25-29.

### Step 2.1 — confirm safety posture before flipping

Open the Cleanuparr UI; navigate to **Settings → General**. Confirm:

- `dry_run = 1` (global dry-run **enabled**) — keep this on for the
  first-pass authorization. Seeker will log what it would have searched
  for without actually triggering Sonarr/Radarr searches.
- Queue Cleaner: **disabled** (do not change — D-17-76 gate).
- Download Cleaner: **disabled** (do not change — D-17-76 gate).

### Step 2.2 — verify Seeker per-instance config

Navigate to **Settings → Seeker** (or the equivalent — UI labels may
shift between Cleanuparr versions). Verify Sonarr + Radarr instances are
present:

- Sonarr: `http://sonarr:8989` (container DNS — F6 doctrine, not
  `mac-mini.internal`)
- Radarr: `http://radarr:7878`

If the instances are not present: STOP. The Sonarr/Radarr API keys
should have been read from the rendered `/vault/secrets/credentials.env`
during container start. Their absence means the sidecar render didn't
populate or the wizard's API-key import step was skipped. Investigate
container env (`docker exec cleanuparr sh -c 'tr "\0" "\n"
< /proc/1/environ | grep -E "^(SONARR|RADARR)_API_KEY=" | sed
"s/=.*/=<set>/"'`) — D-17-26 sub-doctrine.

Verify the staged caps are in place:

- `active_download_limit = 2`
- `min_cycle_time_days = 3`
- `monitored_only = 1`
- Cutoff hunts: **disabled**
- Custom-format hunts: **disabled**

### Step 2.3 — flip Seeker `search_enabled`

In the Seeker config, flip the global enable from `0` to `1` (or
"Enabled" in the UI).

**Keep `dry_run = 1` on for this first pass.** That gives one full
hunt cycle of log-only output to validate behavior before letting Seeker
trigger real searches.

### Step 2.4 — first-pass observability

Watch the cycle land. Cleanuparr writes its activity to container stdout:

```bash
docker logs -f cleanuparr 2>&1 | grep -E "Seeker|search|cycle"
```

Expected within `min_cycle_time_days = 3` (or whatever interval Cleanuparr
uses for its first wakeup — could be sooner on first enablement):

- A "Seeker cycle started" or equivalent line.
- Per-instance API call evidence (queries to `http://sonarr:8989/api/v3/...`
  and `http://radarr:7878/api/v3/...`).
- Dry-run "would search for X items" log lines, NOT actual search-trigger
  posts.

If you see real search-triggers landing in Sonarr/Radarr's queue: stop —
`dry_run` is not on. Re-check Step 2.1.

### Step 2.5 — after a clean dry-run cycle: enable real searches

After at least one clean dry-run cycle (no errors, expected items
identified), navigate back to **Settings → General** and flip:

- `dry_run = 1` → `dry_run = 0`

Save. The next Seeker cycle will trigger real searches.

### Step 2.6 — record the change

Per the reactive-management pattern (`docs/runbooks/buildarr-excluded-services.md`
Step 3), record this as either:

- A commit footnote on whatever repo change closes D-17-49 (lightest), or
- A discrete `docs/_arr-changes/<date>-cleanuparr-seeker-enable.md` note
  if there's no obvious commit to attach to.

The record needs: what changed (Seeker enable + dry-run flip), why
(D-17-49 closure), how to verify (the probe in Step 2.4), and how to
restore (re-flip `search_enabled = 0`, `dry_run = 1`).

## Cleaner modules — deferred (do NOT enable in this session)

Queue Cleaner and Download Cleaner remain disabled until **all four** of
the following are true:

1. `secret/seedbox/qbittorrent` is populated in Vault. Run
   `scripts/provision-seedbox-credentials.sh` (D-17-76; interactive
   password prompt).
2. **D-17-76 commit-2** has landed (cleanuparr policy extension +
   sidecar template `QBIT_*` block + provision-cleanuparr conditional
   readback test). Verify by:
   ```bash
   grep -c "secret/data/seedbox/qbittorrent" \
     config/vault-policies/cleanuparr-policy.hcl
   # expect: 1
   grep -c "QBIT_" docker/vault-agent-cleanuparr/credentials.env.tmpl
   # expect: 2 or more
   ```
3. The cleanuparr sidecar has rendered the new env. After commit-2 lands
   AND the secret is populated, restart the sidecar:
   ```bash
   docker restart vault-agent-cleanuparr cleanuparr
   ls /Users/admin/.vault-agent-secrets/cleanuparr/credentials.env
   grep -c QBIT_ /Users/admin/.vault-agent-secrets/cleanuparr/credentials.env
   # expect: 2 or more
   ```
4. Operator authorizes Cleaner module enablement (a separate operator
   decision after observing Seeker's first real-search cycle).

Until then, leaving Queue Cleaner + Download Cleaner disabled is the
correct posture.

## Rollback — disabling Seeker

If Seeker behavior is wrong after Step 2.5:

1. UI → Settings → General → `dry_run = 1` (re-enable).
2. UI → Settings → Seeker → flip `search_enabled` back to `0` /
   "Disabled".
3. Save.
4. Confirm next cycle is dry-run-only via the probe in Step 2.4.

Cleanuparr does not retroactively undo searches it triggered before
rollback; rollback only stops new ones.

## Cross-references

- `docs/phase-18/d-17-49/SMOKE.md` — runtime state + safety posture record
- `docs/runbooks/buildarr-excluded-services.md` — reactive-management
  record-the-change pattern (Cleanuparr is reactive-managed; no Buildarr
  plugin)
- `~/control-center-stack/stacks/arr-stack/docker-compose.yml:295-355` —
  vault-agent-cleanuparr + cleanuparr service definitions
- `docker/caddy/Caddyfile:149` — `cleanuparr.internal` Caddy front
- `config/vault-policies/cleanuparr-policy.hcl` — current policy
  (Sonarr/Radarr only; D-17-76 commit-2 will extend with seedbox path)
- `docker/vault-agent-cleanuparr/credentials.env.tmpl` — current sidecar
  template (Sonarr/Radarr only; D-17-76 commit-2 will extend with
  `QBIT_*` block)
- F6 (`integration-audit-doctrine.md` Finding 6) — URL-as-credential
  doctrine; container DNS form for arr-stack peers
- D-17-26 sub-doctrine — `/proc/1/environ` redacted-only inspection
  pattern
