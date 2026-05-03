# Capability Audit — ai-platform-dashboard

**Date:** 2026-05-01
**Auditor:** Claude session (operator decision: KEEP)
**Trigger:** D-17-06 agent UI consolidation audit. The D-17-01 stack-audit
hypothesis ("possibly redundant with check-repo-coherence.py") was
flagged for verification. **This audit reverses that hypothesis.**

---

## Section 1 — Tool identification

- **Name:** ai-platform-dashboard
- **Container:** `ai-platform-dashboard`, image
  `integrated-ai-platform/dashboard:latest` (locally built).
- **Compose location:** in-repo at
  `docker/docker-compose-ai-dashboard.yml`.
- **Resource cost (live, 2026-05-01):** 78.8 MiB RAM (0.33% of
  23.42 GiB limit), 0.01% CPU, 2 PIDs. **Lightest of the audited 9.**
  Restart count 0, uptime ~24h.

---

## Section 2 — Probed capabilities

- **Stated purpose:** AI platform operator dashboard.
- **Probe evidence — what it actually is:**
  - Entrypoint: `python3 web/dashboard/server.py --port 8080`.
  - Mounts: `docs/roadmap/ITEMS` + `.git` (read-only style — surfaces
    repo state).
  - Logs: continuous "selfheal cycle 286+" — runs as a daemon driven
    by `bin/selfheal.py`.
  - `bin/selfheal.py` operates the **media pipeline** (MediaHealthChecker,
    AutoFixer, *arr stack, QNAP free-space monitoring, rclone health).
- **D-17-01 hypothesis ("redundant with check-repo-coherence.py"):**
  **REJECTED.** check-repo-coherence is a *static* CLI checker for
  repo state at commit time. ai-platform-dashboard is a *runtime*
  daemon for media-pipeline self-healing. **Different surface, no
  overlap.**

---

## Section 3 — Stack-coverage analysis

| Function                          | Provided by               |
|-----------------------------------|---------------------------|
| Repo coherence checks (static)    | check-repo-coherence.py   |
| Media-pipeline self-heal daemon   | **ai-platform-dashboard** |
| Service portal (bookmarks)        | homepage                  |
| LLM chat                          | open-webui                |

No redundancy. Distinct from check-repo-coherence (static repo) and
from homepage (UI-only portal).

---

## Section 4 — Verdict: **KEEP**

**Rationale:**
1. Stack-audit hypothesis wrong — this is a runtime media-pipeline
   self-healer (not a static checker, not a portal). **D#20
   evidence-over-pattern moment.**
2. Light footprint (~79 MiB RAM, 0.01% CPU) — the cost of keeping is
   negligible.
3. Compose is in-repo and managed.
4. Active workload (selfheal cycle counter advancing) — not idle.

---

## Section 5 — Migration / retirement plan

N/A — KEEP verdict.

---

## Section 6 — Decision log

- **D-17-01 stack-audit hypothesis:** "redundant with
  check-repo-coherence.py" — **REJECTED via D#20 probe (selfheal.py
  daemon, MediaHealthChecker, AutoFixer, arr-stack integration).**
- **Operator decision (2026-05-01):** KEEP.
- **Re-audit trigger:** if media pipeline is decommissioned or moved
  to a different surface, revisit.
