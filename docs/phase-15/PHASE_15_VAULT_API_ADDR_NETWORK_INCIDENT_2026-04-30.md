# Phase 15 — Vault `api_addr` Network Incident Postmortem

**Date:** 2026-04-30
**Severity:** Sev-2 (degraded — multiple containers, no data loss)
**Detected by:** Operator observation of slow ARR apps (radarr/sonarr) and "vault-server deadlock" symptom
**Resolved at:** ~16:55 local
**Author:** Adrian Cox + Claude Code session

---

## Executive Summary

A misconfigured `api_addr` in vault-server (`http://192.168.10.145:8200` — the Mac Mini's host LAN IP — instead of the in-network service name) caused every in-Docker Vault redirect to U-turn through Docker Desktop's userland-proxy. With 38 vault-agent sidecars on the same bridge, the proxy saturated, which serialized **all** host-port-bound services on the host (radarr, sonarr, etc.), producing the ARR slowness. The "vault-server deadlock" symptom that triggered today's recovery attempts was itself caused by this network saturation, not by a broken vault.

**One-line fix:** change `api_addr` from host LAN IP → in-bridge service name (`http://vault-server:8200`) in both the HCL config file and the compose env var.

## Timeline

| Time | Event |
|---|---|
| Earlier in day | Operator notices "vault-server up but :8200 deadlocks." Initiates recovery. |
| ~13:58 | First recovery attempt (`vault-config.hcl.pre-transit-recovery` snapshot taken) |
| ~14:26 | Second recovery attempt (`.BEFORE-RECOVERY-ATTEMPT`) |
| ~14:52 | Third recovery attempt (`.pre-fresh-init`) — fresh init, new keys |
| ~16:17 | HCL last edited (still wrong `api_addr`) |
| ~16:21 | Operator installs `~/bin/troubleshoot` (Ollama qwen2.5-coder:32b) and runs it against the symptom |
| ~16:30 | Diagnostic: vault-server **does** respond on :8200 (200 OK), but in-network requests show 1/5 stall at 6.4s |
| ~16:35 | Operator hypothesis: "this is all items that bind internal Docker IP to a host port — vault was misconfigured by today's recovery and that broke the network" |
| ~16:38 | Confirmed: `VAULT_API_ADDR=http://192.168.10.145:8200` and `api_addr` HCL line both pointed at host LAN IP |
| ~16:43 | Both files patched, `docker compose down/up`, 3-key unseal |
| ~16:55 | Verification: in-network bridge p95 **6.4s → 0.28s**, host-side ARRs 50–122ms steady |

## Symptoms

- **Vault**: container Up but marked `(unhealthy)` — healthcheck timing out at 10s with `barrier init check failed: context canceled` storms during init
- **ARR apps** (radarr, sonarr, prowlarr, etc.): published-port responses on Mac Mini intermittently slow / timing out
- **In-network bridge timing** (5 samples, control-center-net):
  ```
  attempt=1   0.096s
  attempt=2   6.455s   ← TIMEOUT, empty reply
  attempt=3   0.105s
  attempt=4   0.090s
  attempt=5   0.233s
  ```
- **Host-side** (`192.168.10.145:8200`): consistently 9–80ms (looked healthy in isolation)
- **seal-vault** (sibling on same bridge, no host-port redirect issue): 83ms stable

## Root Cause

`vault-server` was advertising `api_addr = "http://192.168.10.145:8200"` — the Mac Mini's host LAN IP — to all clients. Vault uses `api_addr` for HTTP redirects (e.g. when a client hits a non-active node, or for any cross-node API redirect).

With this setting, the in-Docker traffic flow on every redirected client request became:

```
client container (vault-agent-*)
  → bridge: 172.23.0.X → vault-server 172.23.0.5:8200    [direct, fast]
  ← Vault returns 307 redirect to http://192.168.10.145:8200
client container
  → DNS resolves 192.168.10.145 → host LAN IP
  → packet leaves bridge → up host stack → hits Docker Desktop's host-port proxy on :8200
  → userland-proxy translates → back into bridge → vault-server 172.23.0.5:8200
```

That last leg is the bottleneck. **Docker Desktop on macOS runs a userspace TCP proxy** for every `0.0.0.0:PORT->PORT/tcp` binding (this is a known Docker Desktop Mac architectural limitation, not a bug). The proxy serializes connections and has a finite work queue.

With **38 vault-agent sidecars** on the bridge, each refreshing credentials on a token TTL, every refresh round-trip looped through the userland-proxy. Once the queue saturated, **every other host-port binding** on the Mac Mini (radarr 7878, sonarr 8989, prowlarr 9696, etc.) started experiencing the same backpressure — they all share the same Docker Desktop proxy infrastructure.

The "vault-server deadlock" symptom that triggered today's recovery work was itself a downstream effect: vault-server's own internal client (used by gauge collection, KV list, barrier auto-rotation, healthchecks) was redirecting to its own `api_addr` — i.e., looping through the saturated proxy back to itself. That produced the `context canceled` / `context deadline exceeded` errors that *looked* like vault was deadlocked.

## Why Recovery Attempts Failed

Three vault recovery attempts today (13:58, 14:26, 14:52) didn't fix the symptom because:

- They re-initialized vault, rotated keys, and reset Transit seal config
- None of them touched `api_addr`
- Each rebuild left `192.168.10.145` in place, so the userland-proxy U-turn pattern persisted
- The recovery work was diagnosing *vault internals* when the actual fault was in vault's *advertised network address*

This matches the CLAUDE.md operating doctrine warning: **"Stop on any unexpected behavior; surface to user."** Each rebuild went past the unexpected `context canceled` errors instead of asking *why* an in-process Vault was canceling its own contexts.

## Fix Applied

Two files. Both required because HCL takes precedence over env var.

```bash
# 1. HCL config (line 13)
- api_addr      = "http://192.168.10.145:8200"
+ api_addr      = "http://vault-server:8200"

# 2. Compose env (line 25)
-       VAULT_API_ADDR: "http://192.168.10.145:8200"
+       VAULT_API_ADDR: "http://vault-server:8200"
```

Files:
- `~/control-center-stack/stacks/vault/vault-config.hcl`
- `~/control-center-stack/stacks/vault/docker-compose.yml`

Backups: `.pre-network-fix` siblings in same directory.

Restart: `docker compose down && docker compose up -d`, then 3-key unseal.

## Verification

In-network bridge timing (the failing path), 5 samples:

| Sample | Before | After |
|---|---|---|
| 1 | 0.096s | 0.279s |
| 2 | **6.455s (TIMEOUT)** | 0.172s |
| 3 | 0.105s | 0.155s |
| 4 | 0.090s | 0.034s |
| 5 | 0.233s | 0.020s |
| **Failure rate** | **1/5** | **0/5** |
| **P95** | ~6.4s | ~0.28s |

Vault status post-unseal: `Initialized: true, Sealed: false, Threshold: 3, Total Shares: 5`.

Radarr, sonarr, prowlarr — host-side response 9–122ms.

## Lessons

### L1 — `api_addr` must point inside the network the consumers live in

For a single-node Vault on a Docker bridge with in-bridge clients, **set `api_addr` to the in-bridge service name**, not the host's LAN IP. The host LAN IP forces every redirect to U-turn through Docker Desktop's userland-proxy.

If the platform later adds external (non-bridge) clients that need to reach Vault directly, the right answer is dual addressing (separate `api_addr` per listener), not pointing the bridge clients at the host IP.

### L2 — Userland-proxy is shared infrastructure on Docker Desktop Mac

A misconfigured single service can poison the proxy for every other host-port-bound service on the host. Symptoms will appear cross-service (radarr slow, sonarr slow, etc.) and **misdirect troubleshooting** toward "the network is broken" or "Docker is broken" when the actual root cause is one container's traffic pattern.

When multiple unrelated containers slow down simultaneously on a Docker Desktop Mac host, suspect the userland-proxy queue first. Test with sample timing from inside the bridge vs from the host.

### L3 — Recovery work must include a "what changed?" diff

Today's three recovery attempts each took a `.pre-*` backup of the HCL but never diffed against a known-good prior state to ask *what's different*. A 10-second `diff vault-config.hcl vault-config.hcl.pre-block-1.7-backup` would have flagged the `api_addr` change immediately.

**Recommendation:** add to `docs/runbooks/vault-restore-from-backup.md`: before any rebuild, diff current config against the most recent known-good backup and surface every changed line.

### L4 — Generic LLM troubleshooting agents are too generic for this stack

The `~/bin/troubleshoot` Ollama agent installed today produced a textbook 6-layer diagnostic plan (network → container → process → config → storage → logs). It was correct in structure but missed the fault entirely because:

- Its "config" layer prompt was `cat /etc/vault.d/vault.hcl | grep "seal"` — would not have surfaced the `api_addr` line
- Its "network" layer was `docker port` — confirms binding exists, doesn't sample latency
- It had no concept of "in-network vs host-side latency comparison" — the actual signal that broke this case

The generic top-down decision tree is the right shape, but **the diagnostic commands must be specific to the stack's known failure modes**. The v2 template (`~/troubleshoot-agent-v2.txt`) should encode platform-specific probes (Vault `api_addr` check, Docker Desktop userland-proxy timing comparison, etc.) for repeat patterns.

### L5 — "Vault is broken" was a wrong-layer diagnosis

The symptom (port binds, requests time out) looked like a vault-server deadlock. It was actually a *redirect path* problem — vault-server itself was healthy and answering on its listener. The deadlock signature was Vault's *internal* clients hitting the saturated proxy.

When a server appears to deadlock but its listener answers from at least one path, **always test multiple network paths** (in-network, host, sibling container) before assuming the server is the fault.

## Action Items

| # | Item | Owner | Due |
|---|---|---|---|
| 1 | Add `api_addr` validation check to `docs/runbooks/add-new-service.md` | Adrian | Phase 15 |
| 2 | Add pre-rebuild diff step to `docs/runbooks/vault-restore-from-backup.md` | Adrian | Phase 15 |
| 3 | Build platform-specific probe library for `troubleshoot-agent-v2.txt` | Adrian | Phase 15 |
| 4 | One-week verification: re-run bridge-latency probe + ARR response check | Scheduled agent | 2026-05-07 |
| 5 | Audit other services for host-LAN-IP-in-internal-config pattern | Adrian | Phase 15 |

## Related Files

- `~/bin/troubleshoot` — wrapper invoking Ollama qwen2.5-coder:32b with the prompt template
- `~/troubleshoot-agent.txt` — v1 prompt template (generic 6-layer plan)
- `~/troubleshoot-agent-v2.txt` — v2 template (operator-edited; should encode platform-specific probes per L4)
- `~/control-center-stack/stacks/vault/vault-config.hcl.pre-network-fix` — pre-fix backup
- `~/control-center-stack/stacks/vault/docker-compose.yml.pre-network-fix` — pre-fix backup
- `docs/phase-15/PHASE_15_VAULT_BLOCKER_2026-04-30.md` — pre-fix blocker analysis (now resolved)
- `docs/phase-15/PHASE_15_RECOVERY_HANDOFF_2026-04-30.md` — pre-fix recovery handoff (now superseded)
