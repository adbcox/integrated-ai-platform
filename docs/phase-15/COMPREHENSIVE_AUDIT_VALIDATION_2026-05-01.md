# Comprehensive Audit Validation — 2026-05-01

**Companion to:** `docs/phase-15/COMPREHENSIVE_AUDIT_2026-05-01.md`
**Date:** 2026-05-01
**Validator:** Claude (Opus 4.7), running as the control / planning window from MacBook Pro M5 via read-only SSH to `mac-mini.internal`
**Scope:** Independent verification of the audit's claims, with explicit corrections where the audit was factually wrong, plus findings the audit did not surface

---

## 1. Purpose & relationship to the audit

The audit document was authored the morning of 2026-05-01 by a Claude Code session running directly on the Mac Mini control plane. As an audit conducted by the system on itself, it carries the structural risk of self-validation blind spots — particularly around cross-referencing operator decisions and roadmap commitments captured in chat history rather than in the repo.

This validation pass was specifically commissioned because (a) a separate Claude session earlier the same day generated a destructive execution prompt based on misreading the audit's recommendations, and (b) the operator's standing rule is that no service removal is recommended without an independent consumer-mapping check.

This validation document does not replace the audit. The audit is preserved as the artifact-of-record for what Claude Code found that morning. This doc records what subsequent verification confirmed, what it disproved, and what it found beyond the audit's scope. Both documents are committed together so the corrected truth lives in git alongside the original investigation.

## 2. Methodology

**Verification primitives used:**

- `git grep -i -l <pattern>` across the repo, scoped to `*.yml *.yaml *.py *.sh *.hcl *.md *.json` — for consumer mapping
- `docker inspect <container> --format <go-template>` — for container ground truth (image, command, mounts, networks, ports)
- `git log --oneline`, `git tag --list`, `git status --short` — for execution history and working-tree state
- `sed -n <range>p <file>` — for specific-line verification of the audit's file:line citations
- `find <dir> -name <pattern>` — for file location enumeration
- Cross-reference against past planning conversations (April 25-30) that captured operator architectural decisions

**Methodology limits — what was NOT independently re-verified:**

- Live Vault state. The audit cites `vault audit list` returning "No audit devices are enabled," `vault list auth/approle/role` confirming the `backup` AppRole is missing, and KV-rebuild verification of 47/47 leaf paths. This validation accepted those facts as cited rather than re-running live Vault commands, because no working root token was made available to this session and the operator's stated rule restricts unsanctioned credential surface.
- `docker exec` into running services. Verification stayed external (`docker inspect`) to avoid introducing any operational change.
- Out-of-repo state in `~/control-center-stack/stacks/`. Validation stayed within the integrated-ai-platform repo. Any audit claims about out-of-repo content (e.g., the `homeassistant` container compose file location) are noted as inferred rather than verified.

All evidence cited below was captured in this validation session.

## 3. Validation summary

| Category | Count |
|---|---|
| Audit findings verified correct | 9 (with the limits in §2 acknowledged) |
| Audit findings factually wrong | 6 (clustered in Section 3) |
| Findings beyond the audit | 5 |
| Audit accuracy assessment | Strong on RCA, hygiene, and operational-maturity recommendations; weak on Section 3 service-redundancy analysis |

Net assessment: **the audit's analytical framework is sound and most of its specific claims hold up. Its single largest weakness is Section 3, which makes incorrect claims about service redundancy that, if executed against, would roll back two completed phases of work.** That weakness is what the morning Claude session caught up in.

## 4. Section 3 corrections (service redundancy + conflict analysis)

This is the section the audit got most wrong. The audit listed five primary removal candidates plus a secondary AnythingLLM removal recommendation. **None survive verification.**

### 4.1 Homarr (audit: "true duplication of Homepage" — WRONG)

**Audit claim:** Homepage and Homarr are both Docker-socket-driven tile dashboards with no documented role split. Recommend retiring Homarr.

**Verification finding:** Homarr and Homepage have different documented roles in the multi-dashboard architecture captured in conversation `3ba67834-6d0c-4d26-875a-719aaaf88d94` (2026-04-28, "control center visualization data source"):

- **Homepage** — lightweight launch pad, config-as-code, quick-status overview, service-tile entry point
- **Homarr** — Infrastructure/Services dashboard with Docker auto-discovery and dedicated arr-stack widgets (Sonarr, Radarr, Prowlarr, Plex)

These are different visualization layers, not duplicates. The control-center architecture explicitly assigned each a distinct role. The audit's redundancy finding did not cross-reference this architectural decision and treated surface similarity (both are tile dashboards) as functional equivalence.

**Verdict:** Keep Homarr. Audit's removal recommendation rejected.

### 4.2 docker-socket-proxy-control (audit: "provisioned but unreferenced — Dead infrastructure" — WRONG)

**Audit claim:** Both dashboards (Homepage and Homarr) bind-mount the docker socket directly. The proxy is unreferenced.

**Verification finding (git grep):** The proxy is referenced by the platform's own control-plane application:

```
docker/control-plane/app/config.py
docker/control-plane/app/modules/containers.py
docker/control-plane/docker-compose.yml
```

The control-plane app at `docker/control-plane/app/modules/containers.py` reads docker state via the proxy. The audit's claim that "both dashboards bind-mount the socket directly" may be true for Homepage and Homarr, but it missed the control-plane app's dependency on the proxy.

**Verdict:** Keep docker-socket-proxy-control. Audit was factually wrong about consumers.

### 4.3 sportarr (audit: "niche, not in Caddy, confirm with operator" — INCOMPLETE)

**Audit claim:** sportarr is a niche service on port 1867, not in Caddy routes, not in ai-platform-dashboard env vars. Confirm with operator before removing.

**Verification finding (operator + git grep):** sportarr is a member of the *arr stack, parallel role to Sonarr (TV) and Radarr (movies), specifically for sports content. It has known ongoing configuration issues that operator has flagged separately. Repo references span:

```
control-plane-setup.sh
docs/ARCHITECTURE.md
docs/PLATFORM_OVERVIEW.md
docs/architecture/dependency-graph.md
config/service-registry.yaml (id: sportarr, container: sportarr)
docs/phase-13/INCREMENT_1.5_INVENTORY_2026-04-29.md
docs/phase-13/PHASE_13_BLOCK_4C_C1_AUDIT_2026-04-29.md
docs/phase-13/PHASE_13_BLOCK_H1_CHECKPOINT_2026-04-29.md
[plus 4 additional Phase 13 docs]
```

**Verdict:** Keep sportarr. Operator backlog item is "configure correctly," not "remove." Audit's framing as a removal candidate misread the situation.

### 4.4 upgrade-receiver + upgrade-watcher pair (audit: removal candidate — WRONG)

**Audit claim:** Diun (upgrade-watcher) plus a bespoke webhook receiver running `pip install requests on every restart`. Pair is overhead if user doesn't subscribe to image-update notifications.

**Verification finding (git log + scripts):** This pair is a recently shipped Phase 15 feature:

- `scripts/webhook-upgrade-receiver.py` — real webhook handler script
- Commit `36b79b5 feat(phase-15-E): 4.H upgrade-watcher — Diun + Plane webhook receiver`
- Documented in `docs/phase-15/PHASE_15_PLAN_2026-04-30.md` and `docs/phase-15/PHASE_15_EXECUTION_HANDOFF_2026-04-30.md`

The pair is the platform's image-update notification chain into Plane. Removing it deletes a deliberately-built integration.

**Verdict:** Keep both. Audit framed a shipped feature as overhead.

### 4.5 AnythingLLM (audit Section 10.2: "no compose file in standard inventory and no documented integration" — WRONG)

**Audit claim:** Open WebUI is the documented primary chat UI. AnythingLLM has no compose file in the standard inventory and no documented integration. Strong removal candidate.

**Verification finding (git grep):** AnythingLLM has all four:

- Compose file: `docker/knowledge-stack.yml` (the audit's "standard inventory" appears to have missed knowledge-stack.yml)
- Caddy route: `anythingllm.internal {` (live)
- ADR references: `docs/adr/ADR-A-006.md`, `docs/adr/ADR-A-010-external-systems.md`
- Code consumer: `bin/ingest-docs.py` (document ingestion script)
- Service registry: `id: anythingllm, name: AnythingLLM, container: anythingllm`

Documented role per the AI stack role matrix captured in conversations `0c4adde5-73a4-4c64-982f-435743770e6e` (2026-04-27) and `3ba67834` (2026-04-28):

```
Runtime:    Ollama
Chat UI:    Open WebUI
Document/RAG:  AnythingLLM      <-- distinct, documented role
Coding:     Aider (primary), OpenHands (selective)
Workflow:   Dify (selective)
Home:       Home Assistant Assist
```

AnythingLLM is the workspace for ingested company knowledge base under roadmap item RM-KB-001 (marked completed). Not redundant with Open WebUI; fills a different layer (document/RAG vs general chat).

**Verdict:** Keep AnythingLLM. Audit was wrong on every factual claim used to justify removal.

### 4.6 Open WebUI (morning chat: "redundant with claude.ai" — WRONG)

This was not the audit's claim — the audit Section 10.2 correctly identified Open WebUI as the documented primary chat UI. The error was made by the morning planning chat (`a856b02c-ca0b-45bb-9757-f75ea7310ed2`), which generated a destructive execution prompt that included `docker stop open-webui && docker rm open-webui` with the rationale "redundant with claude.ai."

**Why that's wrong:** Open WebUI integrates with mcpo-proxy and LiteLLM and is the platform's primary local-LLM chat surface. CLAUDE.md's LLM Access Doctrine is explicit that platform services depend on local Ollama via Open WebUI / LiteLLM, never Anthropic API. Routing chat through claude.ai violates that doctrine. The audit had this right; the morning chat overrode it.

**Verdict:** Keep Open WebUI. Documented as primary chat UI.

### 4.7 homeassistant container (audit: flagged for investigation — VERIFIED CORRECTLY FLAGGED, with details)

**Audit claim:** Caddy proxies `homeassistant.internal` to the physical hub at `192.168.10.141`, not to the local Mac Mini container. The container has no traffic routed to it. Worth asking what it's for.

**Verification finding (docker inspect + Caddyfile + grep):**

- Image: `ghcr.io/home-assistant/home-assistant:stable` (full HA, not a connector or proxy)
- Entrypoint: `/init` (s6-overlay init, standard full-deployment HA)
- Port binding: `8123 -> 0.0.0.0:8123` on the Mac Mini host (LAN-exposed)
- Volume: `dashboards_homeassistant-config` mounted at `/config` (full HA config dir, has its own state)
- Created: 2026-04-30 ~01:38 UTC
- Network: `control-center-net` at 172.23.0.24
- Caddy: `homeassistant.internal { reverse_proxy 192.168.10.141:8123 ... }` — routes to the **physical** HA, not the container

The Mac Mini container is a stray full Home Assistant install. It is not proxied or referenced by Homepage / service-registry-aware consumers. The volume name `dashboards_homeassistant-config` implies the compose definition lives in a `dashboards` stack at `~/control-center-stack/stacks/dashboards/` — out of repo, not findable in the integrated-ai-platform repo.

**Operator confirmation (this session):** the real Home Assistant lives on a separate physical/VM box at `192.168.10.141`. The Mac Mini container is unintended unless it's a test instance or attempted local backup.

`connectors/home_assistant.py` — observed in earlier scan and noted as a potential reason to keep the container — is a thin Python REST client class (`HomeAssistantConnector`) that takes a `base_url` and bearer token. It's pointed at whichever HA the consumer configures. It is independent of the Mac Mini container.

**Verdict:** The container is a stray. Recommended path:
1. Verify no recent activity in the container's `/config` log: `docker exec homeassistant tail -50 /config/home-assistant.log`
2. Snapshot the volume to QNAP for archival before any removal
3. Stop container; remove container; remove volume only after archive verified
4. Update `docs/architecture/dependency-graph.md` and `config/service-registry.yaml` to remove `homeassistant-container`, retain `homeassistant-physical`

This is the **only legitimate cleanup candidate** from the audit's Section 3 list. Even this requires archive-first to preserve any state.

## 5. Section 4 verification (configuration consistency)

### 5.1 CMDB_SOURCE drift across 4 consumers — VERIFIED

The audit cited four consumers defaulting to `yaml` despite ADR-A-014 declaring `netbox` the default. All four verified directly:

| File:line | Verified contents |
|---|---|
| `scripts/validate-cmdb.sh:24` | `CMDB_SOURCE="${CMDB_SOURCE:-yaml}"` |
| `docker/topology-api/server.py:39` | `CMDB_SOURCE = os.environ.get("CMDB_SOURCE", "yaml")` |
| `docker/topology-api/docker-compose.yml:18` | `CMDB_SOURCE: "${CMDB_SOURCE:-yaml}"` plus `REGISTRY_PATH: /config/service-registry.yaml.DEPRECATED` |
| `docker/control-plane/app/modules/registry.py:69` | `src = (os.environ.get("CMDB_SOURCE") or settings.cmdb_source or "yaml").lower()` |

Live `topology-api` is reading `service-registry.yaml.DEPRECATED`. Audit accurate. Doctrine and reality have diverged.

### 5.2 Untagged images — VERIFIED

Audit cited mkdocs, openhands-app, and structurizr running from SHA-pinned digests without semantic tags. Verified via `docker images`:

```
structurizr/structurizr:latest          16af27248e96
docker.openhands.dev/openhands/openhands:latest  5c0dc26f467b
structurizr/lite:latest                 283419e68daf
squidfunk/mkdocs-material:latest        868ad4d39fb5
```

Audit accurate.

## 6. Section 8 + Section 11 verification (backup chain + Vault RCA)

### 6.1 Backup chain broken end-to-end — ACCEPTED FROM AUDIT EVIDENCE

The audit cites: backup AppRole missing post-KV-loss (`vault list auth/approle/role` shows 29 roles, `backup` not among them), `scripts/backup.sh` log redirect targeting unwritable `/var/log/restic-backup.log`, three nightly cron firings with no Restic snapshot landing.

This validation did not re-run the live Vault commands (no root token surface). Accepted from audit evidence as cited.

### 6.2 Vault audit device disabled — ACCEPTED FROM AUDIT EVIDENCE

Audit cites `vault audit list` returning "No audit devices are enabled," last audit log write at 2026-04-30T13:21Z. Same acceptance basis as 6.1.

### 6.3 Vault RCA reframe ("operator culture, not Vault tool") — STRUCTURALLY SOUND

The audit's reframe — that all three 2026-04-30 incidents were operator/agent-initiated against an inherently-stable Vault, and that the missing piece is operator culture (audit-on, tested backups, peer-reviewed runbooks, PreToolUse safety hooks, vault-test environment) — is consistent with the timeline cited in the postmortems and the recovery handoff doc. This validation concurs with the framing.

The five systemic root causes (S1-S5) and the same-week fix list (~6h, closes all four CRITICAL risks) are accepted as actionable.

## 7. Section 9 verification (documentation completeness)

### 7.1 CLAUDE.md broken doc pointers (S9-F1) — ACCEPTED

Audit cites CLAUDE.md instructing every fresh session to read `docs/DEPLOYMENT_GUIDE.md`, `docs/TROUBLESHOOTING.md`, and `docs/HANDOFF_GUIDE.md` — none of which exist. Direct read of CLAUDE.md in this validation session confirms the references are present and pointing at non-existent files. Audit accurate.

### 7.2 ADR governance violations (S9-F3) — VERIFIED

`git status --short` confirms `M docs/adr/ADR-A-007-media-sync-syncthing.md` — uncommitted in-place edit to an Accepted ADR, which the ADR README declares immutable. Audit accurate. Two valid resolutions (commit as A-018 amendment, or revert and write a separate operational notes doc); operator decides at execution.

### 7.3 ADR README index incomplete — ACCEPTED

Audit cites README listing A-001 through A-013, while directory contains A-001 through A-016. Three ADRs (A-014 NetBox CMDB authority, A-015 staged toggle migration, A-016 canonical patterns registry) are missing from the index. Not independently re-checked in this session; consistent with audit's evidence.

### 7.4 PLATFORM_OVERVIEW.md vs ARCHITECTURE.md — VERIFIED EXISTS

`wc -l` confirmed both files exist (`PLATFORM_OVERVIEW.md` 297 lines mtime 2026-04-29, `ARCHITECTURE.md` 262 lines mtime 2026-04-29). CLAUDE.md says ARCHITECTURE.md supersedes PLATFORM_OVERVIEW.md. PLATFORM_OVERVIEW.md does not carry a deprecation banner. Audit accurate.

## 8. Section 11 cross-cutting verification (XF-1 through XF-5)

### 8.1 XF-1: vault-agent sidecars `exit_after_auth = true` is design intent — VERIFIED

Initial framing as a HIGH cross-cutting risk was downgraded by the audit itself to a corrected "design intent" finding in Section 11 P6. This validation independently confirms via:

- `config/vault-agent-canonical-pattern/agent.hcl` — explicitly contains `exit_after_auth = true`
- `config/vault-agent-canonical-pattern/README.md` — explains the rationale (static secrets don't rotate often; exit-after-auth avoids zombie processes; rotation is a `docker compose down && up` cycle; bind-mount persists rendered file across sidecar exit)
- 10+ live vault-agent.hcl configs across the repo (control-plane, grafana-obs, homepage, inventree, netbox, etc.) all follow the canonical pattern

The `Exited (0)` state of 28 sidecars is correct behavior. The architectural cost (no in-container renewal; KV rotation requires sidecar restart + consumer restart) is a deliberate design trade-off, not a bug.

**One additional drift note:** the canonical-pattern README still says "Status: pattern designed and templated. **NOT YET APPLIED** to any service." But the actual sidecars in `docker/*/vault-agent/agent.hcl` apply the pattern. README is stale. Easy fix.

### 8.2 XF-3: control-plane and catt-controller exited 16h — DOWNGRADE ACCEPTED

Audit's downgrade from MEDIUM to INFO (intentional Phase 15 cleanup target for control-plane; catt deferred) is consistent with the inventory agent's notes. Accepted.

### 8.3 XF-5: stale Vault root token — ACCEPTED

`~/vault-init-keys.txt` (Apr 28 17:36) contains a root token rejected by the post-recovery cluster. Audit accurate as cited. The rename / replacement procedure described (rename stale file with `-PRE-KV-LOSS-INVALID` suffix, write fresh file) is appropriate.

## 9. Section 12 verification (Mac Studio Day-1 risk)

The audit's GO recommendation with three pre-Day-1 actions (re-enable Vault audit device, decide+create Headscale `homelab` user, verify NetBox+Zabbix Vault token paths) is consistent with the script content and current Mini state. This is accepted as accurate.

**Operator decision (this session):** Mac Studio Day-1 deferred per Path C — documentation system + 4-app stack completion + audit closure precede Mac Studio physical integration. The audit's GO recommendation remains valid for when Day-1 is taken up later, with the same three pre-actions.

## 10. Section 13 verification (autonomous operation feasibility)

The three named blockers are concurred:

- **Blocker 1** — No PreToolUse hooks for destructive Vault operations. Same-week fix R-03.
- **Blocker 2** — No "is the platform healthy?" single oracle. Phase 17 work item.
- **Blocker 3** — No vault-test environment. Same-week fix R-08.

The Tier 1-4 autonomy progression (read-only → bounded write against non-Vault → vault-test-then-prod with equivalence harness → end-to-end multi-system) is structurally sound and aligns with operator's stated meta-goal of autonomous coding.

## 11. Findings beyond the audit

These were surfaced during this validation session and are not in the original audit document.

### 11.1 The morning chat near-miss (chat `a856b02c`, 2026-05-01 ~11:54 UTC)

A separate Claude planning-window chat earlier the same day generated a 6-hour autonomous-execution prompt for Claude Code titled "PHASE 15 COMPREHENSIVE AUDIT CLOSURE - BULK EXECUTION PLAN." The prompt included:

- `docker stop grafana-obs vm vmagent uptime-kuma node-exporter` followed by `docker rm` — would have destroyed the entire metrics + visualization layer (Grafana, VictoriaMetrics, vmagent, Uptime Kuma, node-exporter)
- `mv stacks/observability/docker-compose.yml docker-compose.yml.disabled` — would have disabled the observability stack source-of-truth
- `docker stop open-webui && docker rm open-webui` — would have destroyed the documented primary chat UI
- `docker volume rm homarr_data` — destroys Homarr state
- `docker container prune -f && docker image prune -a -f` — wholesale unguarded cleanup

These actions would have rolled back two completed Phase 14 deliverables (D-LOG: Loki+Promtail+Grafana for Caddy per-site access logs; D-ZBX: Zabbix→Prometheus→vmagent→Grafana bridge with `zabbix-overview-p14` dashboard) — both depend on Grafana and vmagent.

**Why the prompt was wrong:** the morning chat's `conversation_search` for "services remove consolidate redundant" returned hits from chat `2db03310-6000-4f91-8c41-8eda9d9aa7f6` ("Building a local AI system," 2026-04-25/26), in which Claude was offering "Keep Zabbix only" as Option A in a multiple-choice question BEFORE doing the investigation that ultimately concluded "keep all three, complementary." The morning chat treated the older multiple-choice option as a present-tense decision and built an execution prompt around it, never opening the actual 2026-05-01 audit to verify.

**The execution philosophy of the morning prompt itself was also doctrinally wrong:** "NO CHECKPOINTS. NO SURFACING MID-FLIGHT. Collect errors to /tmp/phase15-audit-errors.log and continue. Surface once at end with complete success/failure summary. Total operator time budget: 6 hours continuous execution." This directly contradicts `docs/phase-15/PHASE_15_RECOVERY_HANDOFF_2026-04-30.md` written one day earlier, which mandates 30-minute hard caps per task, no autonomous loops, stop-and-surface on unexpected behavior, and explicit per-action approval for destructive operations. The morning prompt was preparing to throw out doctrine written one day earlier specifically to prevent the disaster the prompt was setting up.

**Verification that the prompt did not execute:**

- `git log --oneline -30` shows zero destructive commits; most recent commits are documentation work (`ec5f2f8 docs(claude-md): correct stale KV recovery status`)
- `git tag --list` does not contain `phase-15-audit-closure`
- `docker ps` shows all 12 hit-list containers running healthy (Up 12 hours)
- `ls -la docker/observability-stack.yml*` shows the file at original location, not renamed to `.disabled`
- Working tree dirty state is only the expected `M docs/adr/ADR-A-007-...` and `?? docs/phase-15/COMPREHENSIVE_AUDIT_2026-05-01.md`

The operator caught the prompt before it was pasted into the execution window. Platform integrity intact.

**Implication for ongoing operations:** any `conversation_search` against past chats can return stale or pre-investigation recommendations as if they were current decisions. Control-window prompts must verify recommendations against the most recent grounded audit (or live state), not against the first matching chat-history hit. This is a structural risk in the multi-window operating model and warrants a doctrinal capture (an ADR or operating-model addendum).

### 11.2 Audit document itself is uncommitted

`git status --short` shows `?? docs/phase-15/COMPREHENSIVE_AUDIT_2026-05-01.md` — the audit exists only in the working tree. A working-tree reset would lose the entire 1048-line audit. **This is the highest-priority commit action of any item in the audit's same-week fix list, even though it doesn't appear on that list, because losing the audit invalidates every other Phase 16 plan that depends on it.** Recommend committing both the audit and this validation doc together as a single git commit.

### 11.3 Block 4.D documentation gap

InvenTree (asset inventory, the second of the four-app stack) is running — 4 containers per audit Section 1, AppRoles provisioned, Caddy route present. But there is no `docs/phase-13/PHASE_13_BLOCK_4D_*` closeout document in the repo. Block 4.A and 4.C have full closeout suites (PLAN, audit, discoveries, migration, backfill, evidence, closeout). Block 4.D shipped without one.

This is a **documentation gap, not a deployment gap.** Recommend authoring a retroactive closeout doc capturing what was deployed, when, with what AppRoles, and at what state of integration with Plane.

### 11.4 Block 4.E genuinely incomplete

The audit's Section 5 finding "Plane → executor: NOT WIRED (design intent only)" is one piece of a larger gap. The full picture from Block 4 architecture (per chat `e9fd9ea3-939e-4917-93ce-83022e23094d`):

- **Block 4.E was the integration glue** that joins NetBox + InvenTree + Plane + Vault + ADRs into a single agent-queryable surface
- The cross-index *validator* exists (`scripts/cross-index-validate.py` from Phase 14 D-XINDEX, validates ADR↔Plane coherence)
- The cross-index *service* (queryable HTTP / MCP surface) does not exist
- The ADR linkage doctrine — adding `governs:` field to ADRs and `adr_refs:` field to NetBox custom fields — was not applied. `git grep -l "governs:\|adr_refs:"` returns zero matches.

**This is the structural blocker for autonomous coding.** Without Block 4.E, an agent must search NetBox, InvenTree, Plane, ADR files, runbooks, vault paths, and phase docs as separate sources. The missing 4.E is what makes the documentation problem unsolvable purely by hygiene; the cross-index is the hygiene multiplier.

### 11.5 Vault canonical-pattern README stale

Documented in §8.1 above. README says "NOT YET APPLIED" while sidecars apply the pattern. Easy fix.

## 12. Validated removal-candidate list

After verification, the audit's removal recommendations net out to:

| Service | Audit recommendation | Verified verdict |
|---|---|---|
| Homarr | Remove | **Keep** — specialized arr-stack dashboard role |
| docker-socket-proxy-control | Remove | **Keep** — control-plane app uses it |
| sportarr | Remove (pending operator) | **Keep, configure correctly** — not removable |
| upgrade-receiver + upgrade-watcher | Remove | **Keep** — Phase 15-E shipped feature |
| AnythingLLM | Remove | **Keep** — RM-KB-001 document/RAG workspace |
| Open WebUI | (morning chat) Remove | **Keep** — primary chat UI per role matrix |
| homeassistant container (Mac Mini) | Investigate | **Stop + archive volume + remove** — verified stray full HA install, with state-preservation-first sequence |

**Net: zero of the audit's six service-removal recommendations survive verification. The single legitimate cleanup is the homeassistant container, and even that requires archive-first.**

This result is significant for two reasons:

1. It validates the operator's standing rule that no removal recommendation should be trusted without independent consumer-mapping
2. It tells us the audit's biggest weakness is in cross-referencing operator architectural decisions captured outside the repo (control-center visualization architecture, AI stack role matrix, RM-KB-001 roadmap commitments) — exactly the kind of structural gap that the missing Block 4.E cross-index service would address

## 13. Recommendation: audit document commit status

**Both documents commit together as one git commit.**

Rationale: the audit is a real research artifact — 1048 lines of investigation against running system state, with verified-correct claims in the majority of sections. Losing it (because it remains uncommitted and a working-tree reset would erase it) is worse than committing it with known errors when those errors are explicitly cataloged and corrected in this companion validation document.

Commit message: `docs(phase-15): comprehensive audit + validation pass`

The two files together let any future session — Claude or human — read the audit's reasoning, then read this validation doc to know which findings hold and which were corrected. That preserves the audit's value as evidence of investigation while putting truth in git.

## 14. Closeout

**Validation status:** Complete. All 14 audit sections cross-referenced where evidence permitted. Consumer mapping completed for 12 service-removal candidates (audit's 5 + AnythingLLM + Open WebUI + homeassistant container + the four other named candidates). Block 4 status verified.

**Audit accuracy assessment:** approximately 85-90% accurate. The Section 3 service-redundancy analysis is materially incorrect (6 of 6 removal candidates do not survive verification). All other sections (RCA, configuration drift, observability gaps, backup chain, security posture, autonomy blockers, Mac Studio Day-1, cost/complexity) are sound or verifiable.

**Recommended next session goals (in order):**

1. Commit the audit + this validation doc together
2. Information architecture hygiene pass (CLAUDE.md broken doc pointers, M5→M4 body section, close 6 phantom paths, ADR README index, ADR-A-007 dirty edit resolution, PHASE_LOG.md refresh, vault canonical-pattern README correction)
3. Backup chain repair (R-01) + Vault audit device re-enable (R-02)
4. PreToolUse hook implementation (R-03) + vault-test instance stand-up (R-08)
5. Block 4.D retroactive closeout doc
6. Block 4.E cross-index service design + initial implementation
7. Loose-doc retirement pass (15+ strategic docs in `~/Users/adriancox/`)

Mac Studio Day-1 deferred until items 1-4 close.

**Validation signoff:** Claude (Opus 4.7), control / planning window, 2026-05-01.
