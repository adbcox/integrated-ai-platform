# Capability Audit — sms1obot-mcp-server

**Date:** 2026-05-01
**Auditor:** Claude session (operator decision: KEEP)
**Trigger:** 17.F agent UI consolidation audit (probe of obot trio
members for completeness, even though they are not independently
hardenable per D#30).

---

## Section 1 — Tool identification

- **Name:** sms1obot-mcp-server (obot platform MCP server)
- **Container:** `sms1obot-mcp-server`, image
  `ghcr.io/obot-platform/obot-mcp-server:v0.1.1` (version-pinned ✓).
- **Compose location:** **none** — managed by Obot platform lifecycle
  (D#30 known limitation: cannot be compose-hardened without
  obot-platform configuration API support).
- **Resource cost (live, 2026-05-01):** 92.9 MiB RAM (0.39% of
  23.42 GiB limit), 1.79% CPU, 1 PID. Restart count 0, uptime ~25h.

---

## Section 2 — Probed capabilities

- **Stated purpose:** MCP (Model Context Protocol) server that exposes
  tools to obot agents.
- **Probe evidence — wired and active:**
  - Receives POST /mcp + DELETE /mcp requests from `.19.0.9` (the
    shim).
  - Bidirectional traffic confirms the obot agent runtime is using
    this MCP server live.
- **Stack-coverage hypothesis (from 17.A):** "obot trio member —
  active" — **CONFIRMED.**

---

## Section 3 — Stack-coverage analysis

Part of the obot deployment unit. Without this server, the obot
agent runtime loses MCP tool access. No other tool on the platform
provides this capability for obot.

---

## Section 4 — Verdict: **KEEP**

**Rationale:**
1. Load-bearing for obot — confirmed by live shim → server traffic.
2. D#30 documents that compose hardening is not currently possible;
   accepted trade-off.
3. Pinned to a specific version (`v0.1.1`) — not floating tag.

---

## Section 5 — Migration / retirement plan

N/A — KEEP verdict. (Re-evaluate when obot-platform exposes
configuration API for compose hardening — D#30 closes that gap.)

---

## Section 6 — Decision log

- **17.A stack-audit hypothesis:** "obot trio member" — **CONFIRMED**
  via traffic probe.
- **Operator decision (2026-05-01):** KEEP.
- **D#30 cross-reference:** non-compose-hardened by design (Obot
  managed lifecycle).
