# Capability Audit — sms1obot-mcp-server-shim

**Date:** 2026-05-01
**Auditor:** Claude session (operator decision: KEEP)
**Trigger:** D-17-06 agent UI consolidation audit (probe of obot trio
members for completeness).

---

## Section 1 — Tool identification

- **Name:** sms1obot-mcp-server-shim (nanobot — obot-side MCP shim)
- **Container:** `sms1obot-mcp-server-shim`, image
  `ghcr.io/nanobot-ai/nanobot:v0.0.67` (version-pinned ✓).
- **Compose location:** **none** — managed by Obot platform lifecycle
  (D#30 known limitation).
- **Resource cost (live, 2026-05-01):** 10.38 MiB RAM (0.04% of
  23.42 GiB limit), 0.01% CPU, 11 PIDs. **Lightest container in the
  obot trio.** Restart count 0, uptime ~25h.

---

## Section 2 — Probed capabilities

- **Stated purpose:** nanobot shim — translates between obot's
  internal protocol and MCP server endpoints; pairs with
  `sms1obot-mcp-server`.
- **Probe evidence — active:**
  - Originating IP `.19.0.9` of POST /mcp and DELETE /mcp requests
    arriving at sms1obot-mcp-server confirms this container is the
    live client.
- **Stack-coverage hypothesis (from D-17-01):** "obot trio member —
  shim" — **CONFIRMED.**

---

## Section 3 — Stack-coverage analysis

Part of the obot deployment unit. Without this shim, obot cannot
reach its MCP server. Required for the agent runtime to call MCP
tools. No alternative on the platform.

---

## Section 4 — Verdict: **KEEP**

**Rationale:**
1. Load-bearing for obot trio — traffic probe confirms it is the
   live MCP client.
2. Tiny footprint (~10 MiB RAM).
3. Pinned version (`v0.0.67`) — not floating tag.
4. D#30 documents non-compose-hardened by design.

---

## Section 5 — Migration / retirement plan

N/A — KEEP verdict.

---

## Section 6 — Decision log

- **D-17-01 stack-audit hypothesis:** "obot trio member (shim)" —
  **CONFIRMED.**
- **Operator decision (2026-05-01):** KEEP.
- **D#30 cross-reference:** non-compose-hardened by design.
