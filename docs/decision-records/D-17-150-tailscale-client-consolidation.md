# D-17-150: Tailscale Client Consolidation

## Status

**ACCEPTED [A]** — brew CLI only, remove Tailscale.app

**Decision date:** 2026-05-07 (flight session)  
**Decided by:** Operator (Adrian Cox)  
**Decided at:** GATE checkpoint, after reviewing ADR

---

## Operator decision (2026-05-07 flight session)

**Choice:** Option A (brew CLI only; remove Tailscale.app)

**Reasoning:**
- Doctrine alignment: Tailscale.app is closed-source proprietary; brew CLI tailscale is Apache 2.0 OSS
- Symfonium precedent does NOT transfer: Symfonium fills a true OSS gap (Android music UX); Tailscale.app fills NO functional gap — it's UX-polish over the same daemon, no real capability lost by removing it
- D-17-145 auth recovery runbook depends on CLI access; GUI-only would weaken recovery procedures
- Today's state confusion was caused BY having both clients — Option A eliminates the dual-client failure mode

---

## Context

**Today's discovery (2026-05-07 flight session):**

Two Tailscale clients are installed on MacBook with conflicting configurations:

1. **macOS GUI Tailscale.app** (Homebrew Cask, installed via `brew install tailscale`)
   - ControlURL: `controlplane.tailscale.com` (Tailscale Inc. public control plane)
   - Status: "Connected for 57:05" to empty adbcox@gmail.com tailnet
   - Daemon running as system process
   - Menu bar icon visible

2. **Homebrew CLI tailscale** (installed via `brew install tailscale`)
   - ControlURL: Headscale (self-hosted, configured for `headscale.local.home:8443`)
   - Status: "Logged out"
   - CLI tool interfacing with daemon
   - No GUI

**The problem:**

Both clients share the same daemon on macOS. When Tailscale.app starts, its daemon connects to Tailscale Inc. control plane, overriding the Headscale configuration. When CLI tries to log in to Headscale, it's already authenticated to Tailscale Inc., creating state confusion:

- Tailscale.app thinks you're logged in (but to wrong control plane)
- CLI thinks you're logged out (because daemon is controlled by Tailscale.app)
- Neither client fully works; user must manually `tailscale logout` to switch control planes

**Version mismatch observed:** CLI 1.96.4 vs daemon 1.96.5 (minor, but adds confusion)

**Root cause:** Tailscale.app defaults to Tailscale Inc. control plane on first install. CLI is configured for Headscale. They're competing for the same daemon.

**Architecture context:**
- Doctrine: 100% open-source self-hosted; Proton cloud is the **single exception**
- Current VPN: Headscale (self-hosted on Mac Mini, fully open-source)
- Decision needed: Should macOS Tailscale client be brew CLI only (doctrine-aligned) or Tailscale.app GUI (macOS-integrated)?

---

## Decision drivers (ranked)

1. **Doctrine alignment** — 100% OSS self-hosted (Proton exception only)
2. **Daily-use UX** — menu bar integration, network extension framework (macOS networking), system sleep behavior
3. **Recovery resilience** — which client is most reliable when Headscale is down?
4. **Maintenance burden** — updates, configuration drift, daemon conflicts
5. **Feature completeness** — split tunneling, exit nodes, subnet routes, MagicDNS
6. **Integration with macOS system** — VPN permission prompts, network preferences, sleep/wake behavior

---

## Options

### Option A: Keep brew CLI only, remove Tailscale.app

**Rationale:** Pure Headscale-aligned approach. CLI only, no GUI conflation.

**Pros:**
- **Doctrine alignment:** Only CLI client; always points to Headscale; no Tailscale Inc. confusion
- Daemon has single author (Headscale CLI configures it); no competing GUIs
- Version control is cleaner (one binary version, not daemon + app)
- Smaller attack surface (no macOS GUI framework code)
- Can still use `tailscale up --login-server=headscale.local.home:8443` to configure server
- CLI is fully scriptable for automation (good for runbooks)
- Lighter resource footprint (no macOS network extension for GUI)

**Cons:**
- **No menu bar icon** — can't see connection status at a glance
- **No system network integration** — must manually configure VPN in macOS System Preferences or rely on system sleep behavior
- Can't click "Connect/Disconnect" from menu bar; must use `tailscale up` / `tailscale down` in terminal
- Split tunneling and exit nodes require CLI flags; not discoverable in GUI
- **Weaker macOS integration** — Tailscale's daemon uses macOS network extension framework; CLI doesn't expose all capabilities
- Less familiar to non-technical operators

**Effort to execute:**
```bash
# Remove GUI app
brew uninstall tailscale  # Removes Cask app

# Keep CLI (already installed)
brew install tailscale  # Just the CLI tool

# Configure daemon for Headscale
tailscale up --login-server=https://headscale.local.home:8443
```

**Recovery resilience:** Medium. CLI depends on daemon being healthy. If daemon is hung, must SSH to Mac Mini to restart or diagnose.

---

### Option B: Keep Tailscale.app GUI only, remove brew CLI

**Rationale:** Lean on macOS native integration. Sacrifice OSS purity for UX.

**Pros:**
- **macOS integration:** Menu bar icon, system sleep awareness, native VPN framework
- **Better UX:** Visual connection status, one-click connect/disconnect from menu bar
- **Fewer tools:** Single Tailscale.app client, not confusing duality
- Tailscale.app can use Headscale via `tailscale up --login-server=` flag (GUI app's CLI helper supports it)
- System network extension is more robust than CLI daemon control
- Automatic startup/shutdown with system sleep/wake
- Visual feedback (green/red icon) without opening terminal

**Cons:**
- **Doctrine deviation:** Tailscale.app binary is proprietary (closed-source client). Breaks "100% OSS" rule.
  - Mitigation: Accept as exception (like Symfonium for Android music); Headscale backend stays OSS
- Tailscale.app defaults to Tailscale Inc. on install; must configure Headscale via `tailscale up --login-server=...` after first run
- **Risk:** Tailscale.app updates may revert custom control plane setting or add Tailscale Inc. features
- Updates are frequent (multiple times per month); each update is a potential "drift back to Tailscale Inc." event
- No CLI scripting; harder to automate Tailscale state in runbooks
- Dependence on Tailscale, Inc. for macOS integration code (even if server is Headscale)

**Effort to execute:**
```bash
# Remove CLI
brew uninstall tailscale  # Removes CLI tool

# Keep GUI app (already installed via Cask)
# Or ensure it's installed:
brew install --cask tailscale

# Configure Headscale (one-time)
tailscale up --login-server=https://headscale.local.home:8443
# (tailscale binary still available via GUI app's CLI helper)

# On future updates, may need to re-configure:
# Preferences → Settings → Add custom control server URL (if UI option exists)
# OR manually run `tailscale up --login-server=...` again
```

**Recovery resilience:** Higher for normal use (menu bar UX is solid). Lower for troubleshooting (no CLI = harder to diagnose daemon issues remotely).

---

### Option C: Both clients, accept the confusion, document which is which

**Rationale:** Dual-client as fallback. Accept maintenance burden in exchange for zero removal effort.

**Pros:**
- **Zero removal effort** — keep both as-is
- **Redundancy:** If one client fails, switch to the other
- GUI provides UX when network is stable; CLI available for remote/troubleshooting
- Doesn't require decision-making or surgery on the system right now

**Cons:**
- **Doctrine violation:** Tailscale.app is proprietary (same con as Option B)
- **Ongoing confusion:** Two clients, same daemon, competing for control plane
- **Maintenance burden:** Every Tailscale.app update risks reverting to Tailscale Inc. control plane
- **State management:** Must document which client to use when, which is error-prone under stress
- **Runbook complexity:** Recovery procedures must account for both clients (see D-17-145 runbook)
- **Version drift:** CLI and daemon versions may diverge again
- **Resource waste:** Two installers, two update mechanisms, two config files competing

**This option is not recommended as a permanent state.** It's a tactical "do nothing for now" with clear debt.

---

## Recommendation

**Claude Code recommends Option A (brew CLI only).** Reasoning:

- **Doctrine alignment is most important.** Operator locked architecture: 100% OSS self-hosted except Proton. Keeping Tailscale.app (proprietary binary) violates that; it's not a justified exception like Symfonium (which is the **only** proprietary app in music, and music stack has no good OSS alternative). Tailscale.app is nice-to-have UX, not a gap-filling necessity.

- **Recovery is better.** D-17-145 runbook assumes CLI access to `tailscale` binary for recovery procedures (e.g., emergency re-auth via pre-auth key). CLI is more scriptable and testable in runbooks.

- **macOS integration isn't critical.** Menu bar icon is nice, but operator already has Terminal at arm's reach. One-click isn't essential for a VPN tool used 5–10 times per day.

- **Maintenance is cleaner.** One client, one daemon, one control plane = less to troubleshoot.

**However, if macOS GUI integration is non-negotiable, Option B is viable** — accept Tailscale.app as a proprietary exception (parallel to Symfonium), acknowledge the doctrine deviation, and update master log to codify when proprietary clients are justified.

---

## Consequences per choice

### Option A (brew CLI only):
- **What changes:** Remove Tailscale.app. Use terminal for all Tailscale commands.
- **What stays same:** Headscale backend, Tailscale peers, network connectivity
- **Daily impact:** Menu bar icon gone. Connection status must be checked via `tailscale status` or `tailscale ip`.
- **Recovery:** Cleaner (CLI-based runbooks are more reliable)
- **Doctrine:** Fully aligned (no proprietary clients)

### Option B (Tailscale.app GUI only):
- **What changes:** Remove brew CLI. Use GUI for connect/disconnect.
- **What stays same:** Headscale backend, menu bar UX (now stable)
- **Daily impact:** Menu bar icon back; one-click controls restored
- **Recovery:** Slightly weaker (no CLI; must SSH to Mac Mini to troubleshoot daemon)
- **Doctrine:** Deviation accepted (Tailscale.app is proprietary, like Symfonium exception)

### Option C (both clients, documented):
- **What changes:** Document which client to use when; add runbook section
- **What stays same:** Everything as-is; no removal
- **Daily impact:** Same confusion, but now documented
- **Recovery:** More complex (must troubleshoot both clients' interactions)
- **Doctrine:** Clear violation (Tailscale.app proprietary, no exception justified)
- **Debt:** Clear. Defers real decision indefinitely.

---

## Migration plan (Option A selected)

### WP-150-01a: Critical verification window (24–48 hours, BEFORE removal)

**Safety first:** macOS daemon persistence with brew CLI only is unverified on Darwin 25.4 (MacBook hardware). Establish that the daemon auto-loads and persists before removing Tailscale.app.

**On MacBook:**

```bash
# Step 1: Quit Tailscale.app (but do NOT remove it yet)
osascript -e 'quit app "Tailscale"'

# Step 2: Verify brew CLI daemon is running (auto-launched by launchd)
ps aux | grep tailscale | grep -v grep
# Should show: /opt/homebrew/opt/tailscale/bin/tailscale daemon

# If daemon is NOT running, start it manually:
brew services start tailscale

# Step 3: Verify CLI can reach Headscale
tailscale status
# Should show peers from Headscale (100.64.x.x range)

# Step 4: Test persistence through sleep/wake cycle
# Put MacBook to sleep (⌘+Shift+Eject or System menu)
sleep 30 seconds
# Wake MacBook manually
# After wake, verify:
tailscale status
# Should still show peers connected

# Step 5: Verify reconnection after daemon restart
brew services stop tailscale
sleep 5
brew services start tailscale
sleep 10
tailscale status
# Should show peers after restart

# GATE: If all 5 steps pass, proceed to WP-150-02 (removal)
# If any step fails, diagnose and document before proceeding
```

**Verification checklist (must pass all):**
- [ ] Tailscale.app quit cleanly
- [ ] brew CLI daemon running (`ps aux` shows tailscaled)
- [ ] `tailscale status` returns valid peer list
- [ ] After sleep/wake: peers still listed
- [ ] After daemon restart: peers reconnect within 10 seconds

**If any check fails:** Do NOT proceed to removal. Diagnose the daemon persistence issue (likely launchd plist misconfiguration or macOS system sleep behavior) before removing Tailscale.app as fallback.

---

### WP-150-02: Remove Tailscale.app (AFTER verification passes)

**On MacBook:**

```bash
# Prerequisite: WP-150-01a passed all checks

# Step 1: Final confirmation that brew CLI still works
tailscale status
# Should show peers

# Step 2: Remove Tailscale.app GUI
brew uninstall --cask tailscale

# Step 3: Verify CLI still works (daemon should still be running)
tailscale status
# Should still show peers

# Step 4: Configure Headscale login server (ensure persistence)
tailscale up --login-server=https://headscale.local.home:8443

# Step 5: Create alias for quick status check (optional)
echo "alias ts='tailscale status'" >> ~/.zshrc
source ~/.zshrc

# Done. Use `ts` for quick status, `tailscale` for full commands.
```

**Final verification:**
```bash
ps aux | grep tailscale
# Should show: /opt/homebrew/opt/tailscale/bin/tailscale daemon (NOT Tailscale.app)

tailscale status
# Should show peers connected to Headscale (100.64.x.x range, no 172.x.x Tailscale Inc. range)

brew list | grep tailscale
# Should show: tailscale (CLI only, not cask)
```

---

### WP-150-03: Post-removal validation (1 week)

Track for 1 week:
- [ ] CLI daemon survives reboots without Tailscale.app
- [ ] No drift back to Tailscale Inc. control plane
- [ ] Recovery procedures in D-17-145 work cleanly with CLI-only setup
- [ ] No state confusion or connection drops attributable to dual-client removal

Document findings in Decisions log.

### If Option B selected (GUI only):

**On MacBook:**
```bash
# Step 1: Verify Tailscale.app is installed
/Applications/Tailscale.app --version

# Step 2: Remove brew CLI
brew uninstall tailscale

# Step 3: Open Tailscale.app preferences
open /Applications/Tailscale.app

# Step 4: Configure Headscale (if UI option exists):
# Preferences → Settings → Custom Control Server URL
# Or via terminal (GUI app can still call CLI helper):
/Applications/Tailscale.app/Contents/MacOS/Tailscale up \
  --login-server=https://headscale.local.home:8443

# Step 5: Verify menu bar icon shows "Connected" (green)
# Verify Headscale peers listed

# Done. Use menu bar icon for connect/disconnect.
```

**Note:** Tailscale.app updates may require re-running the `--login-server=` command if it reverts to Tailscale Inc. Track this in a reminder (quarterly check).

### If Option C selected (both, documented):

Create `docs/runbooks/tailscale-client-guidance.md`:
```
## When to use CLI vs GUI

Use CLI (`tailscale` terminal command) when:
  - Troubleshooting daemon/network issues
  - Running automated recovery (D-17-145)
  - At home, on LAN, with Terminal access

Use GUI (Tailscale.app menu bar) when:
  - Normal daily use, quick connect/disconnect
  - On macOS, prefer visual feedback

Known issue: Both clients may conflict. If GUI says "Connected" but CLI says "Logged out", try:
  - `tailscale logout` (from CLI)
  - Quit Tailscale.app (from menu bar)
  - Reopen Tailscale.app
  - Re-run `tailscale up --login-server=headscale.local.home:8443`
```

---

## References

- **D-17-145:** Headscale auth recovery runbook (depends on CLI or GUI working)
- **Master log §3:** Headscale architecture, current control plane URLs
- **Symfonium precedent:** Proprietary Android music client accepted exception (master log §28)
- **Tailscale upstream:** https://tailscale.com/download/mac (Tailscale.app binaries, closed-source)
- **Headscale upstream:** https://github.com/juanfont/headscale (self-hosted control plane, open-source)

---

## Decision summary (for operator)

**Option A (brew CLI only):**
- Doctrine-aligned (no proprietary clients)
- Cleaner recovery procedures
- Trade-off: No menu bar icon; must use terminal for status

**Option B (Tailscale.app GUI only):**
- Better macOS integration; menu bar icon restored
- Accepts proprietary client as exception (like Symfonium)
- Trade-off: Risk of updates reverting control plane; less scriptable

**Option C (both clients, documented):**
- Zero removal effort
- Not recommended long-term; creates ongoing confusion and maintenance debt

---

**DECIDED: OPTION A (CLI ONLY)**

Operator selected on 2026-05-07 (flight session):
- [x] Option A (CLI only) — ACCEPTED [A], brew CLI tailscale retained, Tailscale.app to be removed after verification window

Next: WP-150-01a verification window (24-48 hr, can run anytime on MacBook). WP-150-02 removal after verification passes.
