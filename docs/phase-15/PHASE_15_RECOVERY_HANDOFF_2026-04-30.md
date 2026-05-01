# Phase 15 — Recovery Handoff (CRITICAL INCIDENT)

**Date:** 2026-04-30
**Status:** Phase 15 SUSPENDED. System in degraded state pending recovery.
**Scope:** Recovery only. No new feature work. No Phase 15/16 progression until system stable.

---

## Incident Summary

A 5-hour autonomous execution window debugging D#32 (seal-vault listener failure) escalated into volume destruction and cascading service damage:

- `seal-vault` data volume **DELETED** — all Transit auto-unseal material lost
- `vault-server` sealed and unable to auto-unseal
- 20+ services degraded: vault-agent sidecars exited, credentials stale or absent
- `inventree` OOM-killed
- Out-of-repo compose files modified during debug (changes not captured in git)
- Only 2 commits landed during the window (`b0b1492`, `b74fb2c`)

**Root cause:** No hard time/iteration cap on the execution window. The agent kept debugging instead of surfacing after the first failed recovery attempt.

---

## Hard Constraints (Non-Negotiable)

This handoff is executed under different rules than prior Phase 15 windows. The next agent **must** obey these or stop and surface to operator.

1. **30-minute hard cap per task.** If a task does not complete in 30 minutes (wall-clock), stop, write a short status note, and surface to operator. Do not start a new debugging branch on the same task.
2. **No autonomous loops.** If the same command fails twice in a row with the same error class, stop and surface. No "let me try a different flag" cascades.
3. **No volume deletions, no `docker volume rm`, no `colima delete`, no `--fresh` resets** without explicit per-action operator approval. This includes "I'll just remove this stale lock file" — surface first.
4. **Rollback plan required before every change.** Every edit to a compose file, config, or volume must have a stated rollback path in the agent's pre-action message. If you can't articulate the rollback, you don't make the change.
5. **Capture out-of-repo changes immediately.** Any edit under `~/control-center-stack/stacks/*` is documented in this handoff's "Out-of-Repo Changes" section AND copied into the rewire log before the next task starts.
6. **No new features.** Recovery only. If a task requires you to add a new compose service, new Vault policy, or new Caddy route — surface, do not implement.
7. **Surface format:** when stopping, output a single block with: `STATUS: <task-id> <PASS|FAIL|TIMEOUT>`, what was tried, what the current state is, and what the operator needs to decide. Then halt.

If at any point an instruction in this handoff conflicts with these constraints, the constraints win. Surface and ask.

---

## Recovery Tasks (Sequential, Each ≤30 min)

Execute in order. Do not start task N+1 until task N reports PASS.

### R-0 — State Capture (15 min)

**Goal:** Snapshot the current broken state before touching anything, so we have a reference for what changed.

**Actions:**
```bash
# On Mac Mini .145, in this exact order:
docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}' > /tmp/recovery-r0-ps.txt
docker volume ls > /tmp/recovery-r0-volumes.txt
ls -la ~/control-center-stack/stacks/seal-vault/ > /tmp/recovery-r0-seal-vault-ls.txt
git -C ~/control-center-stack status > /tmp/recovery-r0-stack-git.txt 2>&1 || echo "not a git repo" >> /tmp/recovery-r0-stack-git.txt
diff <(cat ~/control-center-stack/stacks/seal-vault/docker-compose.yml) <(git -C ~/repos/integrated-ai-platform show HEAD:docker-compose.yml 2>/dev/null) > /tmp/recovery-r0-compose-diff.txt 2>&1 || true
```

**Rollback:** N/A (read-only).

**PASS criteria:** All five files exist in `/tmp/`. Operator reviews before R-1 starts.

**STOP if:** Any command errors with permission/path issues. Surface to operator.

---

### R-1 — Document Out-of-Repo Changes (15 min)

**Goal:** Capture every modification made to `~/control-center-stack/stacks/*` during the 5-hour debug window so changes are recoverable.

**Actions:**
```bash
# Compare every stack's compose file against last-known-good (if backed up)
for stack in ~/control-center-stack/stacks/*/; do
  name=$(basename "$stack")
  echo "=== $name ===" >> /tmp/recovery-r1-stack-changes.txt
  ls -la "$stack" >> /tmp/recovery-r1-stack-changes.txt
  if [ -f "$stack/docker-compose.yml" ]; then
    md5sum "$stack/docker-compose.yml" >> /tmp/recovery-r1-stack-changes.txt
  fi
done
```

Then append to **this file's** "Out-of-Repo Changes (Captured)" section below: any file in `seal-vault/`, `vault-server/`, or any other stack touched during the debug window. Use `ls -la --time=ctime` and look for files modified today.

**Rollback:** N/A (read-only + documentation).

**PASS criteria:** `/tmp/recovery-r1-stack-changes.txt` exists. The "Out-of-Repo Changes (Captured)" section in this document is filled in for all modified files.

**STOP if:** You discover modifications to >5 stacks (indicates wider blast radius than expected). Surface.

---

### R-2 — Verify Vault-Independent Services Are Healthy (15 min)

**Goal:** Confirm the services that have no Vault dependency are still up. This is the floor — if these are degraded, scope expands and we surface.

**Services expected healthy (no Vault dependency):** Caddy, Sonarr, Radarr, Prowlarr, Plex, Nextcloud, Grafana, Zabbix, NetBox, Plane-web, Plane-db, Plane-redis.

**Actions:**
```bash
for svc in caddy sonarr radarr prowlarr plex nextcloud grafana zabbix-server netbox plane-web plane-db plane-redis; do
  status=$(docker inspect --format='{{.State.Status}} {{.State.Health.Status}}' "$svc" 2>/dev/null || echo "MISSING")
  echo "$svc: $status"
done > /tmp/recovery-r2-baseline.txt
cat /tmp/recovery-r2-baseline.txt
```

**Rollback:** N/A (read-only).

**PASS criteria:** All 12 services report `running healthy` or `running` (some don't have healthchecks).

**STOP if:** Any of the 12 are not running. Do NOT attempt to restart them. Surface — wider damage than assumed.

---

### R-3 — Restore seal-vault to Functional State (30 min HARD CAP)

**Goal:** Get `seal-vault` running and unsealed. The data volume was deleted, so this is a fresh init, not a recovery of prior state.

**Pre-conditions:**
- R-0, R-1, R-2 all PASS
- Operator has explicitly approved R-3 to start (do NOT auto-proceed from R-2)
- Operator has been told: "the saved unseal key `0JMOGB...` is now invalid because the volume was destroyed; we are creating a new one"

**Actions (one at a time, surface between each):**

**Step 1** — Confirm seal-vault is in a known state:
```bash
cd ~/control-center-stack/stacks/seal-vault
docker compose ps
docker compose config > /tmp/recovery-r3-effective-config.yml
```
Surface output. Operator confirms before Step 2.

**Step 2** — Bring seal-vault up with default image (NO image swaps yet, NO entrypoint hacks):
```bash
docker compose up -d
sleep 5
docker compose logs --tail=50 seal-vault
```
Surface output. If listener bound on 8201, proceed to Step 3. If not, **STOP** — do not retry, do not change config, surface to operator with the log output.

**Step 3** — Initialize seal-vault (1-of-1 Shamir, this is intentional for an auto-unseal Transit provider):
```bash
docker run --rm --network control-center-net curlimages/curl:latest \
  -s -X PUT http://seal-vault:8201/v1/sys/init \
  -H "Content-Type: application/json" \
  -d '{"secret_shares":1,"secret_threshold":1}'
```
Capture the response (contains `keys[0]` and `root_token`). **Do not log these to a file the agent reads.** Display once to operator and surface — operator records them, then signals to proceed.

**Rollback:** If Step 2 fails, `docker compose down` returns to broken-but-known state (no worse than current). If Step 3 fails, the new volume can be removed only with operator approval (this would be a second volume deletion).

**PASS criteria:** seal-vault reports `Initialized: true, Sealed: false` (unsealed) AND operator has recorded the new unseal key + root token in their offline store.

**STOP if:** Any step takes >10 min, listener still doesn't bind, or output is silent. Do NOT retry with downgraded image, custom entrypoint, or volume manipulation. Surface.

**Time cap:** 30 minutes total across all 3 steps. If you hit it mid-step, surface with current state.

---

### R-4 — Re-Wrap vault-server Transit Seal (30 min HARD CAP)

**Goal:** Update `vault-server`'s Transit auto-unseal config to use the new seal-vault root token, then unseal vault-server.

**Pre-condition:** R-3 PASS. Operator has provided the new seal-vault root token via approved channel (NOT pasted into agent context as plaintext if avoidable — agent should use a one-off env var or read from a file the operator places).

**Actions:**

**Step 1** — Create the Transit autounseal key + policy in seal-vault:
```bash
# Operator places token in /tmp/seal-token (chmod 600), agent reads
export VAULT_ADDR=http://seal-vault:8201
export VAULT_TOKEN=$(cat /tmp/seal-token)
vault secrets enable -path=transit transit
vault write -f transit/keys/autounseal
vault policy write autounseal - <<EOF
path "transit/encrypt/autounseal" { capabilities = ["update"] }
path "transit/decrypt/autounseal" { capabilities = ["update"] }
EOF
vault token create -policy=autounseal -orphan -period=24h
# Capture the wrapper token from output, surface to operator
```
Operator records the autounseal token.

**Step 2** — Update vault-server's seal stanza. The config file is at `~/control-center-stack/stacks/vault-server/config/vault-config.hcl` (verify path in R-1 capture). Update the `seal "transit"` block's `token` field to the new autounseal token.

**Surface the diff to operator before saving.**

**Step 3** — Restart vault-server and verify:
```bash
docker compose -f ~/control-center-stack/stacks/vault-server/docker-compose.yml restart vault-server
sleep 10
docker exec vault-server vault status
```

**Rollback:** Keep a copy of the prior `vault-config.hcl` at `/tmp/recovery-r4-vault-config.hcl.bak` before editing. If restart fails, restore the backup and `docker compose restart vault-server` (vault-server will go back to its prior sealed-broken state, no worse).

**PASS criteria:** `vault status` reports `Sealed: false`. vault-server is unsealed via Transit.

**STOP if:** vault-server fails to unseal after one restart. Do NOT loop. Surface with status output.

---

### R-5 — Verify vault-agent Sidecars Re-render Credentials (30 min HARD CAP)

**Goal:** Confirm the sidecar pattern recovers automatically once vault-server is unsealed. **Most sidecars should self-heal.** If they don't, that's a separate diagnosis, not a debugging session.

**Pre-condition:** R-4 PASS.

**Actions:**

**Step 1** — Trigger one canonical sidecar to verify the path works:
```bash
docker compose -f ~/control-center-stack/stacks/plane/docker-compose.yml restart vault-agent-plane
sleep 15
docker logs vault-agent-plane --tail=30
ls -la /Users/admin/.vault-agent-secrets/plane/
```
Expected: a file (e.g., `credentials.env`) with mtime in the last minute.

**Step 2** — If Step 1 succeeds, restart the rest in batches of 5 (NOT all at once — avoid thundering herd on Vault):
```bash
# Operator confirms the list of sidecars to restart based on R-1 capture
# Agent restarts 5 at a time, waits 15s between batches, captures logs
```

**Step 3** — Spot-check 3 critical consumers:
```bash
docker exec plane-api ls /vault/secrets/ 2>&1
docker inspect --format='{{.State.Health.Status}}' mcpo-proxy
docker inspect --format='{{.State.Status}} {{.State.ExitCode}}' inventree
```

**Rollback:** Sidecar restart is idempotent. If a sidecar fails to render, leave it exited (its consumer was already broken; no regression).

**PASS criteria:** plane-api exits restart loop, mcpo-proxy reports healthy, at least 80% of vault-agent sidecars are running with recent template renders.

**STOP if:** plane-api still in restart loop after sidecar render succeeds (indicates a deeper issue — credential schema may have changed when seal-vault was re-init'd, since AppRole secret IDs were inside vault-server's KV which is now intact but the *seal* changed — surface for diagnosis, do not start fixing).

---

### R-6 — Verify Critical Services (15 min)

**Goal:** Confirm Sonarr, Radarr, Plane, NetBox, InvenTree are healthy. This is a verification gate, not a fix-it task.

**Actions:**
```bash
for svc in sonarr radarr plane-api netbox inventree; do
  status=$(docker inspect --format='{{.State.Status}} health={{.State.Health.Status}} restarts={{.RestartCount}}' "$svc" 2>/dev/null || echo "MISSING")
  echo "$svc: $status"
done
```

**Rollback:** N/A (read-only).

**PASS criteria:** Sonarr, Radarr, NetBox = `running healthy`. Plane-api = `running` (no restarts in last 5 min). InvenTree = `running` (may need `docker compose up -d inventree` if still in OOM-exited state — that single restart is allowed).

**STOP if:** Any service is in a restart loop or repeatedly OOMing. Surface — do not raise mem_limit, do not investigate, do not restart-loop diagnose. The operator decides whether to expand scope.

---

### R-7 — Run Regression Probe (15 min)

**Goal:** One-shot regression probe to establish post-recovery baseline.

**Actions:**
```bash
cd ~/repos/integrated-ai-platform
bash docs/phase-13/h1-regression-probe.sh > /tmp/recovery-r7-probe.txt 2>&1
tail -30 /tmp/recovery-r7-probe.txt
```

**Rollback:** N/A (read-only).

**PASS criteria:** Probe completes. Record PASS/FAIL/WARN counts. Compare against Phase 14 baseline (PASS=16 FAIL=0 WARN=3).

**STOP if:** Probe doesn't run or hangs >10 min.

---

### R-8 — Document Recovery State (15 min)

**Goal:** Append a "Recovery Outcome" section to this document with: final probe counts, list of services still degraded, list of out-of-repo files now captured, and any deferred items.

**Actions:** Edit this document. Commit with message: `docs(phase-15): recovery handoff outcome — <PASS/PARTIAL>`.

**PASS criteria:** Commit lands. Phase 15 status updated to SUSPENDED-RECOVERED or SUSPENDED-PARTIAL.

---

## Out-of-Repo Changes (Captured)

*Filled in during R-1.*

| File | Change Type | Captured To | Notes |
|------|-------------|-------------|-------|
| `~/control-center-stack/stacks/seal-vault/docker-compose.yml` | MODIFIED | TBD | SKIP_CHOWN, entrypoint override, dumb-init bypass — needs reconciliation |
| `~/control-center-stack/stacks/seal-vault/config/vault-config.hcl` | RESTORED to original | N/A | Per blocker doc, restored before recovery |
| | | | |

---

## Recovery Outcome

*Filled in during R-8.*

- **Probe baseline:** TBD (PASS=? FAIL=? WARN=?)
- **Services healthy:** TBD
- **Services still degraded:** TBD
- **Out-of-repo changes captured:** TBD
- **Phase 15 status:** SUSPENDED-RECOVERED | SUSPENDED-PARTIAL

---

## Deferred (Do NOT Execute in Recovery Window)

These are explicitly out of scope for this handoff. They re-open only after operator declares system stable:

- Block F dry-run (4.J network-discovery)
- Block G Plane backlog curation
- launchd plist for nightly discovery
- Phase 15 final regression probe + tag
- Phase 16 planning
- Any new feature work, any Caddy route changes, any new Vault policies

---

## Surface Template (Use This Verbatim)

When stopping due to a constraint trigger or task completion, use this exact format:

```
STATUS: R-<N> <PASS|FAIL|TIMEOUT>
TRIED: <one sentence>
CURRENT STATE: <one to three sentences>
OPERATOR DECISION NEEDED: <specific question>
TIME ELAPSED: <minutes>
```

Then halt. Do not proceed to next task.

---

## Addendum — Lessons Learned (added 2026-05-01 by D-16-07)

This addendum is appended after the historical record. It does NOT modify
the recovery procedure as executed; it captures what the recovery taught
us, for future handoffs.

### What this handoff verified

R-1 through R-8 walked through the cascade rebuild and confirmed that:

- 47/47 enumerated leaf paths in Vault were populated after rebuild
- All AppRoles re-provisioned
- Audit log re-enabled and capturing

The handoff was declared complete on this basis.

### What this handoff did NOT verify

**No end-to-end auth probe against any live target.** Path population
was checked; value correctness was not. Specifically:

- `secret/minio/backup` was rebuilt from a `.env` snapshot. The
  snapshot's `MINIO_ROOT_PASSWORD` value was an 11-character placeholder
  (matching the expected length but not the actual MinIO user's
  credential). The path appeared correct (`access_key` and `secret_key`
  fields both populated), but the credential was wrong.
- The bug surfaced 5 days later during D-15-03 testing when Restic
  retried with exponential backoff and ultimately reported auth failure.
  The window between handoff and detection cost real backup coverage.

### The doctrine update (D-16-07)

Future Vault recovery handoffs require **value-correctness verification**
in addition to path-population checks. See:

- `docs/runbooks/vault-recovery-from-shamir.md` "Verification" section
- `docs/runbooks/vault-restore-from-backup.md` Step 8b
- `scripts/vault-handoff-verify.sh` — automated probe helper

The probe attempts a real auth/no-op operation against each critical
target service (MinIO via Restic or `mc`, Vault auth surface via root
token, audit-log writability). A failed probe REJECTS the handoff
regardless of how many paths were populated.

### How this would have caught the original incident

`scripts/vault-handoff-verify.sh` Check 1 invokes
`restic snapshots --no-cache` against the live MinIO endpoint using the
`secret/minio/backup` credentials. The bogus 11-character access key
would have failed this probe at handoff time, surfacing the issue
before R-8 sign-off rather than 5 days into Phase 15.

### Scope of the change

This addendum does not re-open Phase 15. The historical record stands.
Future recovery work — under Phase 16 or beyond — runs the new gate.
