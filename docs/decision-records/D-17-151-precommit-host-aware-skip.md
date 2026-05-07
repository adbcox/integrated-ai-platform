# D-17-151: Pre-commit Hook Host-Aware Skip Logic

## Status

**PROPOSED** — Design document for operator decision

**Decision date:** TBD (operator decision required)  
**Issue triggered:** 2026-05-07 flight session — repeated `git commit --no-verify` due to host-specific hook failures on MacBook

---

## Problem statement

**Today's friction:**

Pre-commit hooks in the repo are designed for the Mac Mini (home server, CI-like enforcement mode). They have hard dependencies on infrastructure that only exists on Mac Mini:

1. **mac-studio-reachable** hook: Pings Mac Studio at 192.168.10.142 to verify home network reachability
   - Works on: Mac Mini (home, LAN-connected)
   - Fails on: MacBook (traveling, no LAN access to 192.168.10.0/24)
   - Current behavior: exits 1 (blocks commit); operator must use `--no-verify`

2. **vault-audit** hook (hypothetical, from master log): Checks ~/Library/LaunchAgents for Vault agent
   - Works on: Mac Mini (Vault agent running, plist installed)
   - Fails on: MacBook (portable, no persistent Vault agent)
   - Current behavior: exits 1; requires `--no-verify`

**Impact:**

- Travel sessions (MacBook only) require `git commit --no-verify` on every commit
- This weakens the safety gate (pre-commit is meant to prevent commits that would break CI)
- Operator must manually remember which hooks apply where
- Risk: if operator forgets to add `--no-verify` when needed, commit fails and disrupts workflow

**Root cause:**

Pre-commit hooks are host-agnostic. They check resources (specific IPs, file paths, services) without first asking "can I even reach this resource?" or "should I skip this check on this hostname?"

---

## Decision drivers (ranked)

1. **Commit gate reliability** — operator should commit on any host without manual flags; gates should adapt to environment
2. **Safety preservation** — do NOT skip checks blindly; skip only checks that are genuinely inapplicable
3. **Operational friction** — minimize operator cognitive load (no "which flags do I need on which host?" decision trees)
4. **Maintenance burden** — adding host awareness should not require per-host config copies or environment variable dance
5. **CI resilience** — GitHub Actions (CI/CD runner) should still run full checks without modification

---

## Options

### Option A: Hostname-based skip

**Rationale:** Each hook checks `hostname` or `uname -n` and exits 0 (skip) if not the target host.

**Implementation sketch:**

```bash
# In each hook entry point (or wrapper script):
HOSTNAME=$(hostname -s)  # e.g., "adrians-macbook-pro"
TARGET_HOST="mac-mini"

if [ "$HOSTNAME" != "$TARGET_HOST" ]; then
  echo "Skipping <hook-name>: host is $HOSTNAME, not $TARGET_HOST"
  exit 0  # Skip (success)
fi

# Otherwise, run the actual check
```

**Pros:**
- Simplest to implement (one-liner per hook)
- No environment variables or config complexity
- Clear, deterministic skip logic

**Cons:**
- **Brittle:** Hardcodes hostnames. If operator changes laptop hostname, hook silently skips on new hostname
- **Overly broad:** Skips checks on ANY non-target host (e.g., a CI runner would also skip if it's not named "mac-mini")
- **False confidence:** If operator is working from a different home server, the hook still skips instead of running
- **Not idiomatic:** CI/pre-commit community prefers capability checks over hostname

**Rollback:** Remove the hostname check, hooks run everywhere again

---

### Option B: Capability-based skip (RECOMMENDED)

**Rationale:** Each hook tests for the resource it depends on. If the resource is unreachable/unavailable, the hook exits 0 (skip) instead of blocking. If the resource is reachable, the hook runs the full check.

**Implementation sketch:**

```bash
# Example: mac-studio-reachable hook
TARGET_IP="192.168.10.142"
TIMEOUT="2"

# Test reachability
ping -c 1 -W "$TIMEOUT" "$TARGET_IP" >/dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "Skipping mac-studio-reachable: $TARGET_IP unreachable from this host"
  exit 0  # Skip (success)
fi

# If we reach here, target is reachable. Run the full check.
python3 scripts/check-repo-coherence.py mac-studio-reachable
exit $?
```

```bash
# Example: vault-audit hook
VAULT_AGENT_PLIST="$HOME/Library/LaunchAgents/com.hashicorp.vault.agent.plist"

if [ ! -f "$VAULT_AGENT_PLIST" ]; then
  echo "Skipping vault-audit: Vault agent plist not found (expected on Mac Mini only)"
  exit 0  # Skip (success)
fi

# Otherwise run the audit
python3 scripts/check-repo-coherence.py vault-audit
exit $?
```

**Pros:**
- **Robust:** Tests REALITY (can I reach this resource?) not labels (what is my hostname?)
- **Idiomatic:** Matches pre-commit community practices (SKIP if precondition not met)
- **Host-agnostic:** Works on MacBook, Mac Mini, CI runner, any new future host
- **Safe:** Fails properly if check logic itself breaks (vs hostname mismatch masking a real problem)
- **CI-compatible:** GitHub Actions runner (different hostname) still runs full checks if resource is available (depends on CI network setup)

**Cons:**
- **Slightly more code:** Each hook needs a "can I reach this?" preamble
- **Timeouts:** Network checks (ping) add latency (but 2-second timeout is acceptable; faster than hook latency usually)
- **Resource-specific:** Some checks may not have an obvious "can I reach this?" test (mitigated by testing a file, port, or service)

**Rollback:** Remove capability tests, hooks run everywhere again (original state)

---

### Option C: Pre-commit config split

**Rationale:** Maintain two `.pre-commit-config.yaml` files — one for Mac Mini (full checks) and one for MacBook (skipped checks). Select via environment variable at commit time.

**Implementation sketch:**

```bash
# At repo root:
# .pre-commit-config.yaml (default, for Mac Mini — run all checks)
# .pre-commit-config-macbook.yaml (reduced, skips host-specific checks)

# In local git config or shell profile:
export PRE_COMMIT_CONFIG_FILE=$([ $(hostname -s) = "mac-mini" ] && echo ".pre-commit-config.yaml" || echo ".pre-commit-config-macbook.yaml")

# Pre-commit should then use:
pre-commit run -c "$PRE_COMMIT_CONFIG_FILE"
```

**Pros:**
- Explicit per-host configuration (no ambiguity)
- Easy to maintain separate check sets
- Each config is pure (no conditional logic inside hooks)

**Cons:**
- **Duplicates config:** Two files to keep in sync; if one is updated, must remember to update the other
- **Fragile:** If one file diverges from the other, commits on MacBook may pass but fail in CI
- **Operator burden:** Requires env var setup, shell profile edits, testing on multiple hosts
- **CI complexity:** GitHub Actions needs to know which config to use (adds conditional logic to CI YAML)
- **Non-standard:** Pre-commit doesn't natively support per-host config selection; this requires custom tooling

**Rollback:** Remove custom config selection, use default .pre-commit-config.yaml everywhere

---

## Recommendation

**Claude Code recommends Option B (capability-based skip).**

**Reasoning:**

1. **Robustness:** Tests reality (can I reach this?) not labels (what's my hostname?). If operator changes hostname, migrates to new laptop, or adds a new location with home-network access, checks still work correctly.

2. **Safety:** A hook that can't find its precondition explicitly says why it skipped. Operator can see "Skipping mac-studio-reachable: 192.168.10.142 unreachable" and make an informed decision (am I supposed to be on the home network?). Hostname-based skip hides this reasoning.

3. **CI-friendly:** GitHub Actions (or any CI runner) with the same network access as home can run full checks without config changes. Hostname-based skip would silently skip on CI.

4. **Maintenance:** Each hook is self-contained; capability check is added once per hook and requires no global config changes or environment variables.

5. **Idiomatic:** This pattern matches how pre-commit community handles platform differences (e.g., `stages:` for CI vs local, or skip guards in hook scripts).

**However**, if simplicity is paramount and operator is certain they will never:
- Change hostname
- Work from a new location with home-network access
- Use additional home servers

Then **Option A (hostname-based skip)** is acceptable with a documented assumption.

**Option C is NOT recommended** — it duplicates config and creates sync burden without meaningful benefit over Option B.

---

## Implementation plan (Option B)

If operator selects B, the work packages are:

### WP-151-01: Design capability tests per hook

For each host-specific hook, design a quick "can I reach this?" test:

| Hook | Precondition test | Timeout | Skip message |
|---|---|---|---|
| mac-studio-reachable | `ping -c 1 -W 2 192.168.10.142` | 2s | "Mac Studio unreachable; skipping reachability check" |
| vault-audit (hypothetical) | `[ -f "$HOME/Library/LaunchAgents/com.hashicorp.vault.agent.plist" ]` | instant | "Vault agent plist not found; skipping audit" |
| launchd-recency | `[ -f /Library/LaunchAgents/... ]` (if Darwin) | instant | "Not on macOS; skipping launchd check" |

### WP-151-02: Modify hook entry points

Edit `scripts/check-repo-coherence.py` or individual hook scripts to add capability checks at the top of each subcommand.

**Pseudocode:**

```python
def mac_studio_reachable():
    """Check Mac Studio reachability. Skip if unreachable."""
    if not can_reach("192.168.10.142", timeout=2):
        print("Skipping mac-studio-reachable: Mac Studio unreachable")
        return 0  # Success (skip)
    
    # If reachable, run full check
    return check_mac_studio_reachability()
```

### WP-151-03: Test on MacBook

Run pre-commit on MacBook (without `--no-verify`). Verify:
- [ ] Hooks with unreachable preconditions skip cleanly
- [ ] Hooks with available preconditions still run
- [ ] All skipped hooks print clear "Skipping..." messages
- [ ] Commit succeeds without manual flags

### WP-151-04: Test on Mac Mini

Run pre-commit on Mac Mini. Verify:
- [ ] All hooks run (no false skips)
- [ ] No regressions in check logic
- [ ] Commit succeeds with full gate

### WP-151-05: Test in CI

Commit to GitHub, verify Actions:
- [ ] CI runs full pre-commit suite (all hooks, no skips)
- [ ] No new failures introduced by capability checks
- [ ] Build passes

---

## Consequences per choice

### If Option A (hostname-based skip):
- **What changes:** Each hook checks `hostname`; adds 1-2 lines per hook
- **Operator benefit:** `git commit` works on MacBook without flags
- **Risk:** Brittle (hostname-dependent); false skips if hostname changes
- **CI impact:** Depends on CI runner hostname (may skip unintentionally)

### If Option B (capability-based skip):
- **What changes:** Each hook adds precondition test (ping, file check, port check)
- **Operator benefit:** `git commit` works on MacBook AND works correctly if hostname changes or new locations added
- **Risk:** Network tests add <2s latency per hook (negligible)
- **CI impact:** Works correctly on CI if network/infrastructure matches home setup

### If Option C (config split):
- **What changes:** Create .pre-commit-config-macbook.yaml; add env var logic
- **Operator benefit:** Explicit per-host config
- **Risk:** Config divergence; sync burden; CI must know which config to use
- **CI impact:** Requires conditional logic in CI workflow YAML

---

## Decision gate

**Operator must choose:** Option A, Option B, or Option C.

**Recommendation standing:** Option B is most robust and maintainable. Proceed with implementation once operator confirms.

---

## References

- **Pre-commit documentation:** https://pre-commit.com/ (platform detection, skip patterns)
- **Repo:** `.pre-commit-config.yaml` at root; hook implementations in `scripts/check-repo-coherence.py`
- **Related:** D-17-150 (Tailscale client consolidation — separate host-awareness decision, but similar pattern of "works on one host, fails on another")

---

**Decision summary for operator:**

**Option A (hostname-based skip):**
- Simplest to implement
- Brittle if hostname changes or new hosts added
- CI may false-skip

**Option B (capability-based skip, RECOMMENDED):**
- Slightly more code per hook
- Robust and idiomatic
- Works correctly on MacBook, Mac Mini, CI, and future hosts
- No environment variables or global config changes needed

**Option C (config split):**
- Explicit per-host config
- Requires duplication and sync discipline
- Not recommended; Option B is superior

---

**STATUS: AWAITING OPERATOR DECISION (A / B / C)**

Next step: Operator confirms choice → WP-151-01 through WP-151-05 execute accordingly.
