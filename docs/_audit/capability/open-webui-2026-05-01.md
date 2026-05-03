# Capability Audit — open-webui

**Date:** 2026-05-01
**Auditor:** Claude session (operator decision: KEEP)
**Trigger:** D-17-06 agent UI consolidation audit (9 candidates probed for
overlap, redundancy, retirement opportunity).

---

## Section 1 — Tool identification

- **Name:** open-webui (Open WebUI)
- **Container:** `open-webui`, image `ghcr.io/open-webui/open-webui:main`.
- **Compose location:** out-of-repo at
  `/Users/admin/control-center-stack/stacks/ai-control/docker-compose.yml`
  (D#15 — rewire-log-required for changes).
- **Resource cost (live, 2026-05-01):** 1.025 GiB RAM (4.38% of 23.42 GiB
  limit), 0.18% CPU, 32 PIDs, 632 MB read I/O. **Heaviest of the
  audited 9.** Restart count 0, uptime ~25h.
- **Operator history:** primary chat UI for the platform's local Ollama
  models per LLM Access Doctrine (CLAUDE.md). Surfaced at
  `webui.internal` via Caddy.

---

## Section 2 — Probed capabilities

- **Stated purpose:** ChatGPT-style web UI for local LLMs (Ollama-native;
  also speaks any OpenAI-compatible endpoint).
- **Currently providing:** primary operator-facing chat UI for the
  platform; consumes models served by Ollama on the Mac Mini host
  network.
- **Active traffic:** running for ~25h continuous; net I/O 107 kB rx /
  5.42 kB tx in the stats sample window — light per-snapshot, but the
  service is the canonical chat surface and operator uses it
  interactively.
- **Stack-coverage hypothesis (from D-17-01):** open-webui is the LLM chat
  UI; no overlap with obot (agent-runner), openhands (autonomous coding),
  or anythingllm (RAG-over-docs). **Confirmed.**

---

## Section 3 — Stack-coverage analysis

| Function                     | Provided by              |
|------------------------------|--------------------------|
| Local LLM chat               | **open-webui** (this)    |
| Agent execution              | obot                     |
| Autonomous coding agent      | openhands-app            |
| RAG-over-uploaded-docs       | anythingllm (under review) |
| Service portal               | homepage                 |
| Operator dashboard           | ai-platform-dashboard    |

No redundancy with the other 8 audited tools. Open WebUI is the
single operator chat front-end.

---

## Section 4 — Verdict: **KEEP**

**Rationale:**
1. Single canonical chat UI for local Ollama models — load-bearing for
   the LLM Access Doctrine (`claude-local` is CLI; open-webui is GUI).
2. No redundant tool covers the same surface.
3. Resource cost is real (1 GiB RAM) but justified by daily operator
   use.

**No migration. No retirement.**

---

## Section 5 — Migration / retirement plan

N/A — KEEP verdict.

---

## Section 6 — Decision log

- **D-17-01 stack-audit hypothesis:** "primary chat UI" — **CONFIRMED**.
- **Operator decision (2026-05-01):** KEEP.
- **Re-audit trigger:** if the platform later standardises on a
  different chat front-end (LibreChat, etc.), or if local Ollama is
  fully replaced by a hosted endpoint, revisit.
