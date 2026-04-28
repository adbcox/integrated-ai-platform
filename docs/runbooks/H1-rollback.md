# H1 Rollback — Runbook

**Highest-severity recovery procedure**. Reverts the entire H1 (Phase 13 Block H1) hardening: Vault audit, auto-unseal, AppRole authentication, Vault Agent sidecars, container hardening.

## DO NOT execute this rollback for

- Single-service issue → use the per-service rollback in the section that introduced it (e.g., `docs/phase-13/h1-rollback-state/<service>-pre-rewire/`)
- Pre-commit hook blocking your work → fix the underlying violation, or `git commit --no-verify` for trivial documentation; **don't disable the hook globally**
- Documentation issue → just edit the doc; rollback is for system state, not text

## DO execute this rollback for

- **Vault auto-unseal failed** and the platform is sealed — first try `docs/runbooks/vault-unseal.md`; if that fails repeatedly, BP-level rollback to pre-Transit Shamir state
- **Multiple services failing** under hardened config (3+ services, not isolated) — try targeted rollback first; full rollback only if cascade
- **Audit logging causing performance issues** — disable audit device first; full rollback if Vault itself is degraded
- **Catastrophic, unrecoverable state** that doesn't respond to per-service rollback

## Procedure

### Step 1: Confirm rollback is the right call

```bash
# Are services restartable individually?
docker ps -a --format 'table {{.Names}}\t{{.Status}}' | head -20

# Is Vault accessible at all?
docker exec vault-server vault status -format=json 2>&1
```

If Vault is reachable and only some services are degraded, prefer per-service rollback.

### Step 2: Pre-flight rollback checks

```bash
# Confirm rollback script exists and is valid
bash -n /Users/admin/repos/integrated-ai-platform/docs/phase-13/h1-rollback-state/rollback.sh
ls -la /Users/admin/repos/integrated-ai-platform/docs/phase-13/h1-rollback-state/
```

### Step 3: Notify (single-developer platform → notify yourself, but log)

```bash
echo "$(date) — H1 rollback executed by admin: <reason>" >> /Users/admin/.platform-logs/incident-log.txt
```

### Step 4: Execute rollback

```bash
bash /Users/admin/repos/integrated-ai-platform/docs/phase-13/h1-rollback-state/rollback.sh
```

The script:
1. Reverts compose snapshots per section (§5, §4, §3, §2, §1, §0)
2. Disables file audit device on Vault
3. Tears down seal-vault container
4. Recreates vault-server with pre-Transit config (will be sealed; manual Shamir unseal required)
5. Restores deleted .env files
6. Reverts pre-commit installation
7. Recreates AppRoles and policies if needed

### Step 5: Manual Shamir unseal of Vault

After rollback, Vault is in pre-Transit state — sealed. Use offline Shamir keys:

```bash
echo "<key-1>" | docker exec -i vault-server vault operator unseal -
echo "<key-2>" | docker exec -i vault-server vault operator unseal -
echo "<key-3>" | docker exec -i vault-server vault operator unseal -
docker exec vault-server vault status
```

### Step 6: Verify pre-H1 state

```bash
# Vault unsealed but on Shamir (no Transit):
docker exec vault-server vault status -format=json | jq '.type'
# Expected: "shamir"

# All services back on .env (visible in compose env: blocks):
grep -l 'POSTGRES_PASSWORD: \${POSTGRES_PASSWORD}' /Users/admin/repos/integrated-ai-platform/docker/*/docker-compose.yml
# Expected: not empty

# Backup script back to broken state:
head -10 /Users/admin/repos/integrated-ai-platform/scripts/backup.sh | grep 'vault-init-keys'
# Expected: line present (broken pattern)
```

### Step 7: Investigate root cause

Before re-applying H1, identify what caused the rollback. Document in `docs/incidents/<date>-h1-rollback.md`.

### Step 8: Re-apply H1 (when ready)

After root-cause fix, re-execute H1 prompts (BP1, BP2, BP3) with the fix incorporated.

## Documentation

After rollback execution, update:
- `docs/incidents/<date>-h1-rollback.md` (new file)
- `~/.platform-logs/incident-log.txt` (append line)
- Phase tracking docs (note the rollback in current phase log)
