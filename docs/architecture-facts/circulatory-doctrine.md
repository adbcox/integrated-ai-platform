# Circulatory architecture doctrine

**Date:** 2026-05-08
**Status:** Active doctrine
**Originating session:** 2026-05-07/2026-05-08 architectural rework
**Authoring framing:** operator metaphor, captured verbatim and elaborated

This document captures the architectural principle the platform follows for hardware/service placement decisions. It is invoked from the master architecture document (`2026-05-08-converged-platform-architecture.md`) and from any subsequent ADR or runbook that touches placement.

## The metaphor

The platform is a circulatory system. Each hardware host is an organ. The platform has two flows: blood (information) and air (compute).

The operator's framing, captured verbatim:

> think of our system like the human circulatory system, we all have a function, we are the best at function, but we aren't good at anything else. Without all we are none. stop trying to have 3 brians, and 3 lungs, when you ned 6 organs, also the blood flow applies to information and the air flow to compute power

## The principle in five rules

1. **One organ per function.** Each hardware host owns ONE primary function. No "two brains, two lungs." Distinct organs each doing their own job.

2. **Each organ is best at its function.** Specialized hardware in specialized roles. Don't ask the kidney to be a lung. Mac Studio is for inference because Apple Silicon is best at it. QNAP is for storage because ZFS + TB4 is best at it. OPNsense (on MS-01) is for network functions because that's what it's the OS for.

3. **All organs needed; no backup organs.** Resilience does not come from duplicate functions. It comes from per-organ health: monitoring, hardware-level redundancy inside each organ (ZFS RAID, ECC RAM, UPS coverage), real backups, and cold-spare hardware for the highest-impact failure modes (Protectli FW4B as cold-spare for MS-01 OPNsense). A human dies if their one heart stops. The system accepts that organ failure cascades — the response is to keep organs healthy and repair them when they fail, not to architect around their failure.

4. **Blood = information; flows must be clean.** DNS queries, secret fetches, auth tokens, API calls, metrics, sensor data, file paths, agent commands — these are blood. Each flow has ONE source authority. Information should reach the right organ for compute without unnecessary detours through other organs.

5. **Air = compute; work happens where it's optimal.** CPU cycles, GPU tensor passes, ZFS scrubs, model inference, transcoding, container scheduling — these are air. Compute happens where the hardware and OS are optimized for it. Storage compute on the storage host. Inference compute on Apple Silicon. CUDA on NVIDIA. Network functions on the network OS.

## How to apply this principle to a placement decision

When a new service candidate appears (or when reconsidering an existing placement), ask:

1. **What domain does this service belong to?** (firewall? home automation? storage? identity? application? inference? CUDA?)
2. **Which organ owns that domain?** (per the master architecture document's organ list)
3. **Does that organ's native extension model fit this service?** (OPNsense plugins, HACS, QPKG, Container Station, Linux Docker, macOS native)
4. **Does the placement keep flows clean?** (Does information have to bounce through extra organs? Is compute happening in the wrong place?)
5. **If no organ owns the domain, what's the fallback?** (The convergence appliance — MS-01 — by default. It hosts what doesn't fit elsewhere.)

If the answer to #3 is "no plugin path exists," the service is a candidate for the convergence appliance's Linux container tier. If the answer to #4 is "flows are crooked," the placement is wrong even if the domain matches — pick a host that keeps flows clean.

## Anti-patterns this principle rules out

- **Duplicate organs as fallback.** "Caddy on OPNsense AND on MS-01 as fallback" is two organs doing one job. Pick one. The other doesn't enter the architecture.
- **Multi-function hosts as default.** "Mac Mini Pro runs Vault server AND is the AI orchestration host" is two functions on one organ when one of them (Vault) needs always-on and the other (orchestration) can sleep. Different requirements → different organs (Vault relocates to MS-01 always-on tier).
- **Vacuum architectural decisions.** Recommending placement without surveying the full fleet is the failure mode this metaphor closes. Always inventory before placing.
- **Service-by-service migrations without doctrinal closure.** Moving a service without retiring its prior home leaves residue (Finding 9 sub-doctrine). Each move pairs with a retirement.
- **Ignoring underutilized hardware.** MS-01 with router-class spec being used as "just a Docker host" violates rule #2. Treat each organ at the level its hardware was designed for.

## How resilience actually comes from this architecture

Counter-intuitively, this is more resilient than a redundant-tier system, because:

- Per-organ health is observable and improvable (you know when a kidney is sick)
- Cold-spare hardware addresses the few highest-impact organs (Protectli FW4B for MS-01 OPNsense; backup chain for QNAP data)
- Organ failures don't have to cascade if the platform's flows are designed to fail gracefully (services with retry logic, Vault Agent secret caching, etc.)
- Maintaining a single organ per function means you actually understand each organ — there's no "fallback host I haven't touched in two years" that may or may not work

## How this principle interacts with other doctrine

- **Finding 22 (cross-host Docker → QNAP-host)** narrows under this principle. The empirical evidence was "split application tier across hosts produces packet-filter pain." The principle forces consolidation, eliminating the split. Finding 22 doctrine is now scoped to its evidence (cross-host Mac-Mini-Docker → QNAP-host) rather than the over-generalized "QNAP can't host applications."
- **Finding 9 (residue is a positive failure mode)** is reinforced. Service migrations under this principle MUST retire the prior placement; otherwise residue accumulates and the "one organ per function" rule is violated by leftovers.
- **Finding T (asset-management substrate gap)** is partially addressed. Knowing each organ's function and hardware spec is foundational asset state.
- **Finding CC (service registry gap)** is the runtime topology surface. The circulatory architecture provides the design-level structure; the service registry provides the runtime structure.

## When this principle fails

The principle is a guideline, not a rule. It can fail in these cases:

- **Operationally complex single-function placement.** Sometimes domain-aligned placement is operationally worse than off-domain. Example from this session: Headscale is domain-adjacent to OPNsense (network/auth), but no plugin exists; running it as FreeBSD package on OPNsense complicates backups and updates. Operational simplicity wins; Headscale stays on the Linux VM (off-domain) on MS-01.
- **Hardware constraints that don't match domain.** If the domain-aligned host lacks capacity, the service goes to the convergence appliance regardless. This isn't a failure of the principle — the principle accepts the convergence appliance as the catch-all.
- **Functions not yet recognized as separate domains.** A new function may need a new organ before there's a host for it. Example: HA voice assist may justify a dedicated edge-AI mini if the operator commits to it as a near-term function.

In each case, document the deviation and why. Don't pretend the principle was followed.

## Status

**Active doctrine** as of 2026-05-08. Applied first to the converged platform architecture (`2026-05-08-converged-platform-architecture.md`). Cross-referenced from all forthcoming ADRs and runbooks in the D-17-211 series.
