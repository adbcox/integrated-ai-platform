# Local AI Workstation Roadmap — Errata

**Companion to:** `docs/architecture-facts/local-ai-workstation-roadmap.md` (ingested 2026-05-09 via `feat/foundation-install-track-2` Stage 0a, KI-B-09 partial close).

**Purpose:** Track defects, stale references, and host-applicability caveats discovered in the canonical roadmap. The canonical doc itself is preserved as-ingested; corrections live here.

**Maintenance rule:** Add an entry whenever a defect is found in the roadmap. Each entry cites the section, the defect, the corrected guidance, and the evidence (incident, source citation, or both).

---

## E-001 — §11.2 Serena install command — wrong package name

**Roadmap text (incorrect):**

```
uv tool install serena
```

**Defect:** The PyPI package `serena` is unrelated to the oraios/serena MCP server. `uv tool install serena` succeeds (installs `serena==0.9.1` from PyPI) but provides no `serena` executable; uv emits "No executables are provided by package serena; removing tool" and uninstalls. The roadmap command is a name-collision trap.

**Corrected command (per official Serena documentation):**

```
uv tool install -p 3.13 serena-agent@latest --prerelease=allow
```

Three differences from the roadmap text:
1. Package name is `serena-agent`, not `serena`
2. Pinned to Python 3.13 (`-p 3.13`)
3. Pre-releases allowed (`--prerelease=allow`)

After install, the `serena` command is available; verify with `serena --help` and initialize with `serena init`.

**Source of truth:**
- https://oraios.github.io/serena/02-usage/010_installation.html (official installation page)
- https://github.com/oraios/serena README, Quick Start section
- The oraios README explicitly warns: "Do not install Serena via an MCP or plugin marketplace! They contain outdated and suboptimal installation commands. Instead, follow our Quick Start instructions."

**Incident evidence:** `feat/foundation-install-track-2` commit `5a63dbf5` ("Stage 5 Serena MCP verification failed"). Resolved by retry with corrected command — Serena 1.2.0 installed cleanly.

**Applies to:** Both MacBook (foundation install complete) and Mac Mini Pro (when its agent stack install runs). Use the corrected command, not the roadmap text.

---

## E-002 — §22 OpenCode source reference — likely incorrect repository

**Roadmap text (suspicious):**

> OpenCode releases: https://github.com/anomalyco/opencode/releases

**Concern:** The canonical OpenCode source per the official site (https://opencode.ai/) is not published from `github.com/anomalyco/opencode`. The roadmap reference may be wrong, stale, or pointing at a fork. Not directly verified to have caused an incident — `feat/foundation-install-track-2` Stage 1 used the official curl install (`curl -fsSL https://opencode.ai/install | bash`) and did not depend on the §22 link.

**Corrected source of truth:**
- Official site and install method: https://opencode.ai/
- Verify the canonical GitHub repo from the opencode.ai docs before depending on §22's URL.

**Status:** Flagged for future verification. If §22's link is confirmed wrong, this errata should be upgraded to "defect" and the canonical repo URL recorded.

**Applies to:** Both hosts. Verify via opencode.ai, not via the §22 GitHub link.

---

## E-003 — §1.3-1.5 Thunderbolt Bridge endpoint — Mac Mini Pro only, not MacBook

**Roadmap text (correct for Mac Mini, inapplicable to MacBook):**

> Mac Studio Thunderbolt Bridge: 10.55.0.1/30
> Mac Mini Thunderbolt Bridge:   10.55.0.2/30
> Preferred Ollama endpoint: http://10.55.0.1:11434

**Clarification (not a defect):** The Thunderbolt Bridge endpoint policy applies **only** to the Mac Mini Pro–to–Mac Studio link. The MacBook (roaming workstation) has no Thunderbolt connection to the Mac Studio. MacBook agent configs use:

- LAN: `http://192.168.10.142:11434` (when on home network)
- Tailscale URL (when off-network — Track 1 work, deferred)
- Local fallback: `http://127.0.0.1:11434` (offline mode)

When Mac Mini Pro install runs, follow §1.3-1.5 as written. When configuring agents on MacBook (or any other roaming host), substitute LAN/Tailscale endpoints for the Thunderbolt Bridge primary.

**Applies to:** Host-specificity callout. The MacBook-to-Mac Mini Pro install handoff must NOT copy MacBook agent configs as-is — the endpoint hierarchy is host-specific.

---

## Maintenance

Append new entries below as defects are discovered. Number sequentially (E-NNN). When a roadmap update is ingested that fixes a defect, mark the relevant errata entry as **Resolved** with the ingest date and commit reference; do not delete (preserves history).
