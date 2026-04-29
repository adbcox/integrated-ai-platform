# State Evaluation and Tooling Recommendation

**Date:** 2026-04-29
**Mode:** Read-only analysis. No artifacts modified, no commits, no execution.
**Audience:** Operator (single-developer platform), with secondary lens for (a) repo/state-cleanup business offering, (b) Georgia Tech OMSCS / Duke MEng AI portfolio review, (c) operator quality-of-life.
**Bar:** Recommendations must be demonstrable to third parties and architecturally defensible — not "good enough for solo use."

---

## PART 1 — STATE REPORT (empirical)

### 1.1 Repo and live-platform inputs

| Source | Result |
|---|---|
| `git log -50 --oneline main` | 50 commits read; latest is `06c57d4` Phase 13 Block 3 P1 audit. `main` does **not** yet contain Block 2.5 (control plane app) or Block 3 P2–P7 (Display & Voice) — those live only on branch `feat/block-2.5-control-plane` (1 commit ahead, `db55b02`) and in the working tree. |
| Phase closing reports | 25 phase-13 docs read, including `PHASE_13_BLOCK_2_CLOSING.md`, `PHASE_13_BLOCK_2_5_CLOSING.md`, `PHASE_13_BLOCK_3_P7_CLOSEOUT_2026-04-29.md`, the H1 hardening series, and `PHASE_LOG.md`. |
| `docs/PLATFORM_OVERVIEW.md` | Last updated 2026-04-27. Claims "Phase 12 Complete" and "55+ services across 6 categories." Pre-dates Blocks 1.x, H1, 2, 2.5, and 3 entirely. |
| `docs/ARCHITECTURE.md` | **Does not exist.** CLAUDE.md "Quick Start" references it on line 19 ("docs/ARCHITECTURE.md - Detailed technical architecture"); `ls docs/ARCHITECTURE.md` returns "No such file or directory." |
| `docs/architecture/` | 3 files: `dependency-graph.md`, `mcp-server-architecture.md`, `portability.md`. None is a top-level architecture document. |
| `docs/road-map/` | Does not exist. `docs/roadmap/ITEMS/` exists but is **empty** (zero files). PLATFORM_OVERVIEW.md line 256 still claims "601 roadmap items (canonical truth)" lives there. |
| `docs/adr/` | 10 ADR files. **A-007 has an ID collision** — two distinct ADRs (`ADR-A-007.md` "External systems should be adopted where commodity fit is strong" and `ADR-A-007-media-sync-syncthing.md` "Syncthing replaces rclone SFTP"). |
| `docs/phases/` | 2 files (`phase-1-10-summary.md`, `phase-11-complete.md`). `docs/PHASE_LOG.md` covers Phase 7–16. Phase numbering is mixed (`Phase 12 Zabbix`, `Phase 16 Vault`, then jumps to `Phase 13 Block 1.x..Block H1..Block 2..Block 2.5..Block 3`). |
| `config/service-registry.yaml` | 65 entries declared (service IDs). Last edit: working tree (`M`) — adds control-plane entry; CATT controller is **not yet registered**. |
| Compose files | 18 docker-compose files across `docker/` (some are stacks: `observability-stack.yml`, `knowledge-stack.yml`, `obot-stack.yml`, `zabbix-stack.yml`; some are per-service). |

### 1.2 Live platform (queried 2026-04-29)

```
Running containers (docker ps):     47
Caddy active routes (admin :2019):   38 *.internal hosts
Vault top-level KV paths:            28 (anythingllm, arr, audit, control-plane,
                                        github, grafana, headscale, homeassistant,
                                        litellm, macmini, mcp, minio, nextcloud,
                                        obot, open-webui, openhands, openweathermap,
                                        opnsense, plane, plex, qnap, resilio,
                                        restic, seedbox, strava, syncthing,
                                        vaultwarden, zabbix)
Vault policy files:                  27 (config/vault-policies/*.hcl)
Vault Agent rendered token dirs:    19 (~/.vault-agent-secrets/<svc>/)
Plane CE total issues:             1100 (8% Done — 88; 92% Backlog — 1012)
Plane CE workspace / project:        iap / "Roadmap" (id dbcd4476-…)
```

### 1.3 Drift inventory (claim vs. reality)

#### A. Service registry vs running containers

19 running containers are **not in `service-registry.yaml`**:
```
cadvisor, catt-controller, docker-plane-api-1, docker-plane-beat-1,
docker-plane-db-1, docker-plane-minio-1, docker-plane-redis-1,
docker-plane-web-1, docker-plane-worker-1, docker-socket-proxy-control,
grafana-obs, homeassistant, openhands-app, plex-mcp, seal-vault,
sms1obot-mcp-server, sms1obot-mcp-server-shim, vault-server, vm
```

Some are renames of registered IDs (registry says `vault`, container is `vault-server`; registry says `victoriametrics`, container is `vm`). Some are real omissions:
- **`catt-controller`** — delivered Block 3 P6, never registered.
- **`grafana-obs`** — delivered Block 2 §P3, registry has `grafana` instead.
- **`docker-socket-proxy-control`** — delivered Block 2.5, never registered.
- **`cadvisor`** — delivered Block H1; registered? grep says no.

The registry's `iap-dashboard` entry has **no backing container** — that service has been replaced by the Block 2.5 `control-plane` container (different name, different code, different port pattern). Registry has both entries; only one is real.

#### B. Architecture-doc claims vs. reality

`docs/PLATFORM_OVERVIEW.md` (last touched 2026-04-27) is doctrinally stale. Sample drift:

| PLATFORM_OVERVIEW claim | Reality (2026-04-29) |
|---|---|
| "Phase 12 Complete" | Phase 13 Block 3 closed; H1 hardening done; control plane delivered |
| "55+ services across 6 categories" | 47 containers; service-registry.yaml has 65 declared entries |
| "Mac Mini M4 Pro" | CLAUDE.md says **M5** (2026-04-29) |
| "Last updated 2026-04-27" | True — but every block since has changed the architecture |
| "OpenHands: Stopped" | Running (16 hours uptime) |
| "LiteLLM Gateway / Open WebUI: Currently stopped" | Both running and healthy |
| References to Anthropic API in LiteLLM | Removed in commit `682736b` (Phase 13.5 Local Orchestration) |
| `docs/ARCHITECTURE.md` referenced | File does not exist |
| `docs/roadmap/ITEMS/` "601 roadmap items" | Directory exists but is empty (Plane CE is now the source of truth, with 1100 items) |

#### C. Block 3 P7 closing report claims vs. Vault reality

P7 says: *"`secret/meross/*` exists in Vault if/when needed"* and *"`secret/warmup/*` exists in Vault if/when needed."*

Empirical: `vault kv list secret/meross` and `secret/warmup` both return **empty `{}`**. Those Vault paths do not exist. The closing report is wrong — a third-party reviewer running `vault kv list` would catch this immediately.

#### D. CLAUDE.md hygiene rules vs. enforcement

CLAUDE.md "Secrets Management" rules state: *"No `.env` files containing credentials. Pre-commit hook (`detect-secrets`) enforces this on tracked files."*

Empirical:
- **Pre-commit hook is installed** (`.git/hooks/pre-commit` executable, `.pre-commit-config.yaml` present, `detect-secrets v1.5.0` in plugin list).
- **The hook does NOT catch the actual exposure.** `config/service-registry.yaml` lines 363 and 382 contain plaintext arr API keys (32-char hex, `2731353744504eb0a5d4225b7c40dfc6` for sonarr, `2a3636f0d3b44ee48082c96298dc5194` for radarr). I ran `detect-secrets scan` against the file directly. Result: **zero hits**. The registered HexHighEntropyString plugin's default entropy threshold doesn't flag these, and the KeywordDetector doesn't match comment-form `notes: API key XXX` syntax.
- The leak has been visible since Phase 12 (commit `e2125e0`, 2026-04-XX). Block 2.5 P1 audit explicitly **flagged it for separate remediation**; that remediation has not happened in subsequent blocks.
- `secret/arr/{sonarr,radarr,prowlarr}` Vault paths exist alongside the plaintext, so the situation is "key written to Vault, plaintext also still committed in repo, hook doesn't catch it."

This is a **demonstrable hygiene-rule-vs-enforcement gap**, not a hypothetical one. A reviewer (engineer, security auditor, admissions reader) cloning this repo and running `git log -p config/service-registry.yaml | grep -E '[a-f0-9]{32}'` would find the keys.

#### E. Branch hygiene

`feat/block-2.5-control-plane` carries db55b02 (Block 3 P2–P7) on top of `main`, plus 6 paths of uncommitted Block 2.5 work. Block 2.5's own closing report mandates "do not commit until Block 3 lands on main" — Block 3 has now landed (on the same branch), so the gate has tripped, but the commit hasn't been issued. Net: `main` is doctrinally one full block + one half-block behind reality, and the only artifact carrying Block 2.5 is the working tree of one machine.

### 1.4 Plane CE roadmap content

| Metric | Value |
|---|---|
| Total issues | 1100 |
| State distribution | Backlog 1012 (92%), Done 88 (8%), all other states 0 |
| Priority distribution | medium 825, high 220, urgent 44, low 11, none 0 |
| Distinct labels in use | 0 (no item has any label assigned, despite 21 labels being configured in earlier deployment) |
| Top theme prefixes | `RM-TESTING-*` 418, `RM-UTIL-*` 330, `RM-UX-*` 110, `RM-USERMGMT-*` 110, `RM-UI-*` 88, plus `RM-AUTO-*`, `RM-CLI-*`, `RM-MONITOR-*` (11 each), and a small `_NO_PREFIX` tail |

Sample top-of-backlog (urgent priority, sorted desc): `RM-AUTO-MECH-001` automotive repair assistant, `RM-CLI-031` roadmap CLI search, `RM-MONITOR-031` AI training-jobs widget, `RM-UX-010` CSV roadmap export. Heterogeneous scope — items range from feature-grade to test-coverage chores to one-off utilities. No clean separation of "platform infrastructure" vs "application features" vs "experiments."

The `[TEST] CMDB + AnythingLLM integration validation` item (sequence 1431, urgent) is itself a roadmap item flagging the absent CMDB. The user has, in their own roadmap, recorded that this gap exists.

### 1.5 Documentation fragmentation summary

Architecture / state knowledge currently lives in:

```
CLAUDE.md                                    (doctrine + current phase line)
docs/PLATFORM_OVERVIEW.md                    (stale; 2026-04-27)
docs/PHASE_LOG.md                            (Phase 7–16 prose log)
docs/ARCHITECTURE.md                          (referenced but does not exist)
docs/architecture/                            (3 narrow-topic markdowns)
docs/adr/                                    (10 ADRs, 1 ID collision)
docs/phase-13/                               (25 working docs of varying status)
docs/phases/                                 (2 historical summary docs)
docs/runbooks/                               (10 procedural docs)
docs/known-issues/                           (4 KIs)
docs/troubleshooting/common-issues.md
docs/performance/baseline-metrics.md
config/service-registry.yaml                 (CMDB-shaped — 65 entries, 19-container drift)
docs/roadmap/ITEMS/                          (referenced as canonical, empty)
Plane CE                                     (1100 issues, separate source of truth)
```

Total: 74 markdown files in `docs/`, plus the YAML registry, plus Plane. A third-party reviewer asking "what is this platform?" has no single entry point and at least three contradictory current-state claims (CLAUDE.md, PLATFORM_OVERVIEW.md, the latest phase-13 closing doc). A reviewer asking "what's planned?" gets two answers: an empty `docs/roadmap/ITEMS/` and a 1100-item Plane backlog with 0 labels.

### 1.6 Recurring problems (synthesized)

1. **Doctrine debt outpaces commits.** Each block produces a closing report that updates *itself* and CLAUDE.md, but PLATFORM_OVERVIEW.md and ARCHITECTURE.md (the docs a third party reads first) drift by 1–3 blocks before catching up. ARCHITECTURE.md has never been written.

2. **Service-registry as CMDB is brittle.** `config/service-registry.yaml` is hand-edited YAML. It claims 65 services; reality is 47 containers with 19 not represented. There's no schema validation, no diff-against-live job, no UI. `scripts/validate-cmdb.sh` exists but PLATFORM_OVERVIEW.md is the only thing that calls it "the CMDB."

3. **Roadmap content has no taxonomy.** 1100 Plane items with 0 labels, 92% in Backlog, no separation of platform vs feature work. The roadmap was bulk-imported (commit `eb19cb1`-era) and hasn't been curated since. A third-party reviewer can't read intent off it.

4. **Hygiene rules exist but enforcement has blind spots.** Pre-commit hook installed; `detect-secrets` plugin set is comprehensive; baseline file present. Yet the Sonarr/Radarr keys in service-registry.yaml are plaintext, in main, with no detection. The rule is policy, not lived constraint.

5. **No structured "current state" surface.** The Block 2.5 control-plane app (`control.internal`) is the closest thing — it queries Vault, Docker, audit logs, etc. live. But it's an action surface for the operator, not a queryable state-of-record for a reviewer or a future "repo cleanup as a service" customer.

6. **ADR maintenance has slipped.** A-007 ID collision. A-009 numbering jumps. No ADR for the Block 2.5 trigger-file pattern, the Block 3 voice-stack architecture, or the deprecation of the `iap-dashboard` service.

---

## PART 2 — TOOLING GAP EVALUATION

### 2.1 Is this a tool gap, a process gap, or a structural gap?

**It is all three, but the binding constraint is structural: there is no single source of truth for current platform state that is queryable, structured, and demonstrable.**

Process gaps (doctrine refresh, registry curation, ADR hygiene, label discipline) are real but solvable with discipline alone if the operator chooses. Tool gaps (better detect-secrets rules, schema-validating the registry) are point fixes. Neither addresses the underlying issue: **the platform's "what exists, how it relates, why it's there" knowledge is split across YAML, Markdown, Plane, and operator memory, and no surface integrates them.**

For solo use, distributed knowledge is tolerable — the operator carries the integration in their head. For the three target audiences (cleanup-services prospects, OMSCS / MEng admissions readers, future ops partners), the *absence of a single integrated surface* is the problem worth solving. That problem is solved at industry scale by a **CMDB layered with an architecture-documentation tool**, not by either alone.

### 2.2 Evaluation criteria (rigor bar)

| Criterion | Rationale |
|---|---|
| Open source, self-hostable | Stack ethos; matches every existing platform service |
| Demonstrable to third parties | Clean UX, structured queryable data, navigable URLs |
| Architecturally defensible | Industry-standard pattern (CMDB / DCIM / IaC documentation) — recognized by reviewers |
| Sustainable solo | Low-effort to keep current; ideally driven from machine-readable sources |
| Integrates with Plane CE | Roadmap stays in Plane; tool consumes/links rather than replaces |
| Integrates with the repo | Compose files, ADRs stay in git; tool reads or links rather than mirrors |

### 2.3 Candidates considered

#### Category A — CMDB / DCIM (structured "current state of everything")

| Tool | Verdict | Notes |
|---|---|---|
| **NetBox** (DigitalOcean) | **Strong fit** | Industry-standard DCIM/CMDB. Models devices, IP addresses, services, contacts, tenants, custom fields. PostgreSQL + Redis + Django. REST + GraphQL APIs. Open source (Apache 2.0). Used at scale (Cloudflare, Equinix). Has a very clean UI. Self-hosts via docker-compose in <30 min. The MCP / API surface allows synchronization from `service-registry.yaml` and `docker ps`. |
| **i-doit** (CE edition) | Adequate | Older PHP stack, more focused on classical IT-asset management; weaker API ergonomics than NetBox. |
| **Ralph** (Allegro) | Adequate | Django-based DCIM; less active community than NetBox. |
| **GLPI** | Mismatch | Service-desk first (tickets, helpdesk); CMDB is bolt-on. Heavier than needed. |
| **Snipe-IT** | Mismatch | Asset-tracking (laptops, licenses), not service-topology CMDB. |

#### Category B — Architecture documentation

| Tool | Verdict | Notes |
|---|---|---|
| **Structurizr Lite** (Simon Brown) | **Strong fit** for diagrams/decisions | C4 model. Diagrams-as-code (Structurizr DSL — text file in repo). Generates context/container/component/dynamic views. Docker image (`structurizr/lite`); reads a `workspace.dsl` file. Produces interactive web view. The DSL file lives in git, so doctrine drift becomes a diff. Used at Capital One, ING, etc. |
| **MkDocs + Material theme + plugins** | Strong fit for narrative | Pure-markdown static site generator. Plugins: `mkdocs-mermaid`, `mkdocs-awesome-pages`, `mkdocs-git-revision-date-localized`, `mkdocs-macros`. Could re-render `docs/` into a navigable site. Industry-standard (FastAPI, Pydantic, Material itself use it). |
| **BookStack** | Acceptable | Good UX, but uses an internal database — pulls knowledge *out* of git, which violates ADR-A-006 ("repo docs are canonical"). |
| **DokuWiki / Wiki.js** | Acceptable | Same concern as BookStack — separate datastore breaks the "repo is canonical" stance. |
| **Backstage** (Spotify) | Overweight | Heavyweight Java/Node stack with TechDocs + Service Catalog. Solves the integrated problem perfectly *at company scale* — but maintenance burden for a solo operator is real. Probably the right answer in 2 years; wrong answer today. |

#### Category C — Hybrid / spans both

| Tool | Verdict | Notes |
|---|---|---|
| **NetBox + Structurizr Lite + MkDocs** | **Recommended combo** | Each tool does what it's best at; they integrate via simple URL links and machine-readable exports. NetBox is the system-of-record for "what exists." Structurizr is the system-of-record for "how it's organized and why." MkDocs renders runbooks, ADRs, and phase logs. Plane CE remains the system-of-record for "what's planned." |
| **Backstage + TechDocs + Service Catalog** | Defer | Same coverage, but the maintenance and bring-up cost is too high for a solo operator. Worth re-evaluating after Phase 14. |

### 2.4 Recommendation

**Adopt the NetBox + Structurizr Lite + MkDocs trio.** Roll them out in that order, one block per tool, behind the canonical Vault Agent / Caddy / `cap_drop` / Vault-policy doctrine. Existing Plane CE and the repo stay as they are.

#### Why this matches the empirically-discovered need

| Discovered problem | How the recommendation addresses it |
|---|---|
| Service-registry drift (19 containers unregistered, 1 phantom) | NetBox becomes the source-of-truth. A nightly job (or pre-commit) reconciles `docker ps` and `caddy admin :2019/config` against NetBox; drift produces actionable diffs, not silent rot. |
| No `docs/ARCHITECTURE.md`, fragmented architecture knowledge | Structurizr Lite renders the C4 model from a single `workspace.dsl` file in `docs/architecture/`. A reviewer gets a context → container → component drill-down. Diagrams update from text — no "stale diagram" failure mode. |
| 74 markdown files with no entry point | MkDocs with Material renders all of `docs/` into a navigable site (`docs.internal` via Caddy). ADRs, runbooks, phase logs, known issues all become searchable; the index is `mkdocs.yml`. |
| Hygiene rule vs. enforcement gap (arr keys) | Out of scope for these tools — but adopting NetBox forces "registry of credentials by service" to be modeled, which surfaces the leak as a cardinality mismatch (key in NetBox secret-relation, also in YAML file → diff job catches it). Real fix is still tightening detect-secrets config; see §2.6. |
| 1100-item, 0-label Plane backlog | Out of scope for these tools — Plane CE stays. But NetBox can store cross-references: each Plane item that maps to a service gets a back-link. |
| ADR-A-007 collision; A-009 numbering | MkDocs surfaces the ADR index as a navigable list; collision becomes immediately visible at build time (nav rendering breaks, forcing the fix). |
| No demonstrable artifact to a third party | NetBox UI + Structurizr web view + MkDocs site = three URLs that, together, present the platform's structure, history, and state without requiring the reader to clone a repo. |

#### What it does NOT solve (honest scope)

1. **It does not write the architecture or the docs.** The DSL file, the MkDocs nav, and the NetBox model are all *vehicles*. The operator still has to author the C4 levels, curate the ADRs, and decide what NetBox object types matter. The benefit is that the work is now durable and reviewable; the work itself is not eliminated.
2. **It does not curate the Plane backlog.** 1100 items, 0 labels, 92% backlog. NetBox can link back to Plane but cannot triage on the operator's behalf. That remains a separate discipline pass.
3. **It does not replace the live operator control plane** (`control.internal`, Block 2.5). The control plane is for *acting*; NetBox is for *recording state and intent*. Both have a role.
4. **It does not eliminate the registry leak class of problems.** Tightening detect-secrets configuration, reviewing the baseline, and adding YAML-file-aware regex rules are independent work — necessary regardless of what tooling is added.
5. **It does not fix git-history exposure.** The Sonarr/Radarr keys are in the repo's git history; only `git filter-repo` (with explicit user approval) addresses that.
6. **It does not collapse the 74 markdown files.** It reorganizes them under a navigable index. Reducing fragmentation requires the operator to merge or retire docs.
7. **It does not change Plane CE's role.** Plane remains the roadmap source of truth. NetBox does not replace it.
8. **It does not auto-trigger from compose changes.** A reconciliation job has to be written; it is not free. The job is small (an hour or two per source) but it is real work.

#### Deployment effort estimate (canonical pattern)

Each component would be deployed via the existing platform doctrine — Vault Agent sidecar, Caddy `*.internal` route, `cap_drop: [ALL]`, `no-new-privileges`, `read_only` where image supports, mem_limit calibrated, scoped Vault policy + AppRole, and a pre/post regression-probe gate. The CLAUDE.md "Add new service" runbook applies verbatim.

| Component | Effort | Notes |
|---|---|---|
| **NetBox** | 6–10 hours | PostgreSQL, Redis, gunicorn, RQ worker (4 containers in stack). Initial schema population: device types (mac-mini, qnap, nuc, opnsense), service objects (47 mapped from `docker ps`), IP addresses, custom fields for `compose_file` and `vault_path`. One-time importer from `service-registry.yaml`. Reconciliation cron (`docker ps` → NetBox API) is ~50 lines of Python. |
| **Structurizr Lite** | 2–3 hours | Single container, mounts a `workspace.dsl` file. Initial DSL: Person + 1 Software System + 4 Containers (Mac Mini control plane, NUC, QNAP, OPNsense) + ~12 Components below them. Caddy route. Ongoing maintenance is editing one text file per architectural change. |
| **MkDocs + Material** | 3–4 hours | Builder container (or static-site generator at commit time) + nginx/Caddy server. `mkdocs.yml` nav structure. Mermaid + git-revision plugins. Could be triggered by a git hook on push to main, or via a small build container. ADR collision must be fixed before nav builds cleanly — that's a forcing function, not a blocker. |
| Reconciliation jobs | 2–4 hours | One Python script per source: `docker ps` → NetBox; `caddy :2019/config` → NetBox; Vault `kv list` → NetBox custom fields (hash-only). Scheduled via launchd or cron. |
| **Total** | **13–21 hours** | One block. Suggest: a single coordinated **Phase 13 Block 4: Documentation + State Surface**, with the three tools as ordered sub-phases. |

Storage, memory, and network footprint are all small. NetBox is the heaviest (~500 MB image, ~200 MB DB once populated). Structurizr Lite is ~250 MB. MkDocs serves static HTML (negligible). All three fit on the Mac Mini without straining Colima's 16 GiB allocation.

#### What changes about platform discipline if adopted

1. **`config/service-registry.yaml` becomes derived, not authoritative.** NetBox is the source; the YAML file is regenerated for `topology-api` consumption. Drift detection becomes a CI / cron concern, not a manual audit.
2. **Architecture changes require a `workspace.dsl` edit** before the closing report is accepted. This is the same forcing-function approach as detect-secrets — the diff is visible in PR review.
3. **ADRs must build cleanly** in MkDocs nav. ID collisions break the build; the operator catches them at edit time, not when a reviewer notices.
4. **A reviewer (admissions reader, prospective customer, future colleague) can be handed three URLs** — `netbox.internal`, `architecture.internal`, `docs.internal` — and answer 80% of "what is this platform?" without needing the operator present.
5. **PLATFORM_OVERVIEW.md retires.** Its content lives in MkDocs (narrative), Structurizr (diagrams), and NetBox (live state). The tendency for a single hand-edited overview file to drift is structurally eliminated.
6. **Phase closing reports cite NetBox object IDs and Structurizr view URIs**, not free-text service names. This is a small but real defensive-engineering shift.

#### What stays unchanged

- **Plane CE remains the roadmap source of truth.** No items are migrated; NetBox links *into* Plane via custom fields.
- **The repo remains the source of truth for code, configs, ADRs, runbooks, and phase logs.** MkDocs renders them; it does not relocate them. ADR-A-006 doctrine is preserved.
- **Vault remains the secrets store.** NetBox stores hash-only references where it stores anything secret-adjacent at all.
- **Caddy, the Mac Mini control plane, and all the existing observability stack** are untouched.
- **CLAUDE.md doctrine** is unchanged in substance. The "Project Structure" section gains three new pointers; the platform rules are unmodified.

### 2.5 Demonstrability lens (per-audience)

**Repo / state-cleanup business offering.** A prospective customer asks "what would you do with our environment?" The answer becomes: "the same thing I did for mine — stand up NetBox to inventory what you have, Structurizr to render the architecture you actually run, MkDocs to make your existing documentation findable, and reconcile-jobs to keep them honest." The personal platform becomes the demo. *This is a directly sellable artifact.*

**OMSCS / MEng AI portfolio.** Admissions readers respond to systems thinking and rigor. A self-hosted NetBox + Structurizr + MkDocs trio integrated with a Vault-backed credential model and a cron-driven drift-reconciliation pipeline is a *legible artifact of engineering judgment* — it shows the candidate identified a problem (fragmentation), evaluated multiple solutions (the candidate matrix in §2.3), chose tools used in industry, and integrated them defensibly. The C4 model in particular is widely taught and recognized.

**Operator quality of life.** The forcing functions (Structurizr edit before block-close, ADR build-time collision detection, NetBox drift cron) catch the problems the operator currently has to remember to check. The operator's working memory is freed for work the tooling can't do.

### 2.6 Independent next steps (separable from this recommendation)

These are necessary regardless of whether the recommendation is adopted:

1. **Tighten detect-secrets configuration.** Lower the HexHighEntropyString threshold for YAML files; add a custom regex rule for `(api[_-]?key|API_KEY)\s*[:=]\s*[a-f0-9]{32,}`; rebuild the baseline. Verify against the known-leaked Sonarr/Radarr keys.
2. **Rotate Sonarr / Radarr / Prowlarr API keys** and scrub the registry. Evaluate `git filter-repo` on history with explicit user approval.
3. **Commit and merge the Block 2.5 working tree**; tag at the merge boundary. The branch is the single point of failure for ~12 hours of finished work.
4. **Curate the Plane backlog.** Apply the existing 21-label set to the 1100 items; reduce the urgent priority count from 44 to <10; close the 88 done items if they're truly done.
5. **Resolve the ADR-A-007 collision** before MkDocs adoption (or it'll surface there anyway).

These five items are scoped tightly enough to land in a single hygiene block before or after the tooling block.

---

## Decision request

Three discrete questions for the user:

1. Adopt **NetBox + Structurizr Lite + MkDocs** as the next architectural block (Block 4)? Yes / no / pick a subset.
2. Order: tools-first (Block 4 = NetBox, then 4.5 = Structurizr + MkDocs) or hygiene-first (sweep §2.6 first, then tools)?
3. Acceptable to retire `docs/PLATFORM_OVERVIEW.md` once MkDocs + Structurizr cover its content? (Migration path, not deletion — content moves; ADR-A-006 stays intact.)

No further action will be taken until these are answered.
