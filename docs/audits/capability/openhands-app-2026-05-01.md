# Capability Audit — openhands-app

**Date:** 2026-05-01
**Auditor:** Claude session (operator decision: KEEP)
**Trigger:** D-17-06 agent UI consolidation audit. The D-17-01 stack-audit
hypothesis ("looks like a Grafana clone — possibly redundant") was
flagged for verification. **This audit reverses that hypothesis.**

---

## Section 1 — Tool identification

- **Name:** openhands-app (OpenHands — autonomous coding agent UI)
- **Container:** `openhands-app`, image
  `docker.openhands.dev/openhands/openhands@sha256:5c0dc26f467bf8e47a6e76308edb7a30af4084b17e23a3460b5467008b12111b`
  (digest-pinned).
- **Compose location:** in-repo at
  `docker/openhands/docker-compose.yml`.
- **Resource cost (live, 2026-05-01):** 571.9 MiB RAM (13.96% of 4 GiB
  limit), 0.16% CPU, 10 PIDs, 256 MB read I/O. Restart count 0,
  uptime ~25h.

---

## Section 2 — Probed capabilities

- **Stated purpose:** OpenHands is a coding agent that operates a
  sandboxed dev environment, edits files, runs tests, and proposes PRs
  — the "autonomous coding" surface.
- **Probe evidence — what it actually is:**
  - Process: `uvicorn` serving on `:3000`.
  - Container env: `LLM_BASE_URL` points to host Ollama; agent uses
    a local model.
  - Image label: `org.opencontainers.image.source` =
    `https://github.com/All-Hands-AI/OpenHands` (canonical project
    name verified against image metadata).
- **D-17-01 hypothesis ("Grafana-like UI, redundant"):** **REJECTED.**
  The "dashboard-like" URLs in earlier surface inspection are
  OpenHands' own conversation/event endpoints, not Grafana clones.
  This is the autonomous coding agent — a distinct capability from
  every other tool on the platform.

---

## Section 3 — Stack-coverage analysis

| Function                       | Provided by              |
|--------------------------------|--------------------------|
| Autonomous coding (file edits, |                          |
| test runs, PR proposal)        | **openhands-app** (this) |
| Local LLM chat                 | open-webui               |
| Agent execution (general)      | obot                     |
| RAG-over-docs                  | anythingllm (review)     |

No overlap. No other tool runs autonomous code-modifying agents.

---

## Section 4 — Verdict: **KEEP**

**Rationale:**
1. Hypothesis from stack audit was wrong — this is OpenHands, not a
   Grafana clone, not a dashboard. **D#20 evidence-over-hypothesis
   moment.**
2. Unique capability on the platform: autonomous coding agent backed
   by local Ollama (no cloud dependency).
3. Resource cost (~570 MiB RAM) is reasonable for an LLM-backed agent.
4. Compose is in-repo and managed.

**No migration. No retirement.**

---

## Section 5 — Migration / retirement plan

N/A — KEEP verdict.

---

## Section 6 — Decision log

- **D-17-01 stack-audit hypothesis:** "Grafana-like UI, redundant" —
  **REJECTED via D#20 probe (uvicorn:3000 + Ollama LLM_BASE_URL +
  github.com/All-Hands-AI/OpenHands image source)**.
- **Operator decision (2026-05-01):** KEEP.
- **Future re-audit trigger:** if the platform adopts a different
  autonomous coding agent (Goose, Aider as primary, etc.), revisit
  consolidation.
- **Doctrine note:** this is the canonical worked example for D#20 —
  capability evidence beats stack-level pattern matching.
