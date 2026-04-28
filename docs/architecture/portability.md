# Heterogeneous Architecture Portability

The Integrated AI Platform is designed to span multiple hosts:

- **Mac Mini M5** (current): macOS via Colima/Docker Desktop. Primary host today.
- **Threadripper** (pending): Linux. Compute, ML training, build workloads.
- **Mac Studio M3** (pending): macOS. AI/ML inference, second-region failover.

## Per-host Vault config

Vault behavior differs across kernels. Per-host configs live in `config/vault-configs/`:

| File | Target | Notable |
|---|---|---|
| `vault-config-macmini.hcl` | Mac Mini (Colima) | `disable_mlock = true`; `IPC_LOCK` not added |
| `vault-config-linux.hcl` | Threadripper | `disable_mlock = false`; compose adds `cap_add: [IPC_LOCK]` |

The active config for vault-server is symlinked or copied to `vault-config.hcl` at deploy time based on host detection.

## Lifecycle managers

- macOS: `launchd` plists in `~/Library/LaunchAgents/` (Vault audit rotation, docker events capture, etc.)
- Linux: `systemd` units (templates pending Threadripper deployment)

## Container patterns

All Phase 13 H1 §6 sidecar patterns are tested on macOS/Colima and designed to be Linux-portable:
- Host bind-mount paths use absolute Mac paths today; will be parameterized per host
- `cap_drop: [ALL] + targeted cap_add` works identically across Linux and Colima
- Vault Agent + AppRole pattern is platform-neutral

## Anti-patterns to avoid

- macOS-specific paths hardcoded outside `config/host-overrides/` (creates Linux portability debt)
- Capabilities that work on Linux but silently fail on Colima (validate per-platform)
- launchd-only timing assumptions (Linux deployments will use systemd timers)

## Heterogeneity flag in canonical pattern README

Every architectural decision in `config/vault-agent-canonical-pattern/README.md` is portability-flagged. New patterns must be tested on the platform of the target service or marked KNOWN-LIMITATION with rationale.
