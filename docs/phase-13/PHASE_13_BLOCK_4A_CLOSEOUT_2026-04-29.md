# Phase 13 Block 4.A — Pre-Merge Reconciliation: Closeout

**Date:** 2026-04-29
**Branch (now consolidated):** `feat/block-2.5-control-plane` → `main` (fast-forward)
**Tag:** `v13-block-3-close` at `bed7d26`
**Status:** Complete; main fast-forwarded; regression probe PASS=15 FAIL=0 (no new WARN).

## Goal

Bring `main` up to reality. Block 2.5 (operator control plane) had been built and validated but not committed pending Block 3 merge. Block 3 (`db55b02`) had been committed onto the Block 2.5 feature branch by an earlier parallel-execution mistake. Both needed to land on `main` as a single coherent linear history, with three doctrine corrections applied along the way.

## Phases

### A0 — Pre-flight verification (read-only)

Confirmed:

- Working tree state: 1 modified + 6 untracked paths, all six matching the Block 2.5 expected set per the planning artifact's clarification #1.
- Branch divergence: 1 commit ahead of `main` (`db55b02`), 0 behind. Pre-execution state. Post-execution would be 5 ahead per planning artifact.
- `origin/main` and local `main` in sync (`06c57d4`).
- No rebase/merge in progress.

Surfaced two flags:
- The planning artifact's "5 commits ahead" framing is post-execution, not pre-execution. Resolved.
- `db55b02` (Block 3 close) sitting on the Block 2.5 branch is the known artifact of an earlier window mistake; A6 fast-forward consolidates it intentionally. Resolved.

### A1 — Block 2.5 inspection (read-only)

Inspected each of the 6 staged paths:

| Path | Type | Lines | Summary |
|---|---|---|---|
| `config/service-registry.yaml` | M | +43 | Append `control-plane` service entry |
| `config/vault-policies/control-plane-policy.hcl` | new | 78 | Read-only on operator hash, arr keys, restic, minio; explicit-deny on policy/AppRole writes |
| `docker/control-plane/` | new | 41 files | FastAPI app + 3-service compose stack (vault-agent sidecar, socket-proxy, app), HTMX frontend, host-launcher LaunchAgent + scripts |
| `docs/phase-13/PHASE_13_BLOCK_2_5_CLOSING.md` | new | 129 | Closing report |
| `docs/phase-13/PRE_BLOCK_2_5_FOUNDATION_AUDIT_2026-04-28.md` | new | 607 | Foundation audit |
| `docs/phase-13/STATE_AND_TOOLING_RECOMMENDATION_2026-04-29.md` | new | 296 | State/tooling recommendation |
| `scripts/provision-control-plane.sh` | new | 165 | Idempotent Vault policy + AppRole + operator-password provisioner |

Manual credential scan (literal API keys, high-entropy strings, `sk-*`/`ghp_*`/`AKIA*`/`hvs.*`/`pat-*` prefixes, 32+ hex strings): clean. The only credential surface in the staged files is the provision script's argv-safe Argon2 hash handling (Python child reads password, hash piped via stdin to `vault kv put` — never on argv).

### A2 — Block 2.5 commit + push

- Staged 47 files, ran `pre-commit run --files <staged>`: all 8 hooks passed (trailing-whitespace, end-of-file-fixer, check-yaml, check-json, check-added-large-files, detect-private-key, detect-secrets, yamllint).
- detect-secrets passed clean — no halt-and-surface scenario triggered.
- Committed `a251161`: `Phase 13 Block 2.5: operator control plane`. 47 files changed, +4,729 lines.
- Pushed to origin as new upstream branch `feat/block-2.5-control-plane`.

### A3 — Doctrine refresh

Single commit `45efc6d`: `Block 4.A doctrine refresh`. 4 files changed, +9 / −6.

- `CLAUDE.md` "Current Phase" line: Block 2 → "Blocks 2 + 2.5 + 3 closed; Block 4.A pre-merge reconciliation in progress". Platform Rules — Non-Negotiable section untouched per spec.
- `docs/PLATFORM_OVERVIEW.md`: phase line updated; services count 55+ → 60+; last-updated 2026-04-27 → 2026-04-29. Minimal edit per spec; full overhaul deferred to Block 4.C.
- ADR-A-007 ID collision resolved: bare `ADR-A-007.md` ("External systems") renamed to `ADR-A-010-external-systems.md`. The Syncthing ADR (`ADR-A-007-media-sync-syncthing.md`) keeps A-007. Renumber annotation added in renamed file's header. README index updated to reflect both ADRs plus the previously-missing A-009 (Vault) entry.

Cross-references checked via `grep -r "ADR-A-007" docs/`:
- `docs/adr/README.md` → updated (was pointing at renamed file).
- `docs/known-issues/KI-RETIRED-rclone-sftp.md` → no change (references the Syncthing ADR which keeps A-007).
- `docs/phase-13/STATE_AND_TOOLING_RECOMMENDATION_2026-04-29.md` → no change (describes the collision itself; left as snapshot).
- `docs/phase-13/PHASE_13_INVENTORY_2026-04-28.md` → no change (references Syncthing ADR).
- `docs/phase-13/historical/INFRASTRUCTURE_INVENTORY_2026-04-27.md` → no change (frozen historical snapshot).

PLATFORM_OVERVIEW.md "Mac Mini M4 Pro" vs CLAUDE.md "Mac Mini M5" contradiction noted but left alone — out of A3's "minimal edit" scope; defers to Block 4.C full overhaul.

### A4 — Service-registry drift reconciliation

Single commit `232171b`: `Block 4.A registry reconciliation`. 1 file changed, +155 / −2.

Live ground truth: `ssh admin@192.168.10.145 docker ps`, 47 running containers. Drift computed as `comm -13` on container-name field of registry vs live names.

**Important deviation from spec count:** the planning artifact cited "19 unregistered containers". On strict container-name comparison, only **5** names drifted. The discrepancy comes from methodology: the spec's "19" appears to derive from `id:`-vs-container-name comparison, but most spec-mentioned renames (`vault`→`vault-server`, `victoriametrics`→`vm`, `grafana`→`grafana-obs`, `plane`→`docker-plane-*`) were already correct — those use `id:` for logical service name and `container:` for docker process name, which is the registry's intended pattern. Documented in commit message.

Five new entries added:

| ID | Container | Decision | Rationale |
|---|---|---|---|
| `docker-socket-proxy-control` | `docker-socket-proxy-control` | sidecar of control-plane | Block 2.5 deployed it but missed registering. |
| `catt-controller` | `catt-controller` | first-class | Block 3 P6 deliverable. |
| `cadvisor` | `cadvisor` | first-class with documented `privileged: true` exception | per CLAUDE.md container-hardening note. |
| `seal-vault` | `seal-vault` | support-service | Vault Transit auto-unseal; deployed Phase 7, undocumented until now. |
| `plex-mcp` | `plex-mcp` | first-class | MCP bridge for Plex library queries; vault policy already existed. |

Phantom entry handled:
- `iap-dashboard` annotated with `deprecated: true, superseded_by: control-plane`. Entry retained for history per spec default.

Cosmetic fix: control-plane header comment was indented at 4 spaces (under topology-api's `notes:` block) instead of 2 spaces (list-item level); corrected.

Post-A4 drift state: **0 unregistered running containers**. 70 services in registry total (was 65). YAML parses clean (`yaml.safe_load` succeeds; pre-commit yamllint passes).

Out of scope per spec, confirmed not touched: no schema-validation infrastructure, no new tooling — that is 4.B/4.C work.

### A5 — Block 3 P7 falsifiable-claim correction

Single commit `bed7d26`: `Block 4.A: correct Block 3 P7 closeout falsifiable claim`. 1 file changed, +2 / −2.

Empirically verified the false claim before correcting:

```
$ ssh admin@192.168.10.145 docker exec vault-server vault kv list secret/meross
No value found at secret/metadata/meross
$ ssh admin@192.168.10.145 docker exec vault-server vault kv list secret/warmup
No value found at secret/metadata/warmup
```

Both `secret/meross/*` and `secret/warmup/*` were asserted to "exist if/when needed". Replaced with: "Vault paths for Meross/Warmup credentials will be created during the device-population block; not present today (verified `vault kv list secret/meross|warmup` empty 2026-04-29)."

### A6 — Branch consolidation

Pre-execution state: branch 5 commits ahead of main, 0 behind. Local `main` in sync with `origin/main`.

Mechanic per spec:
```
git checkout main
git merge --ff-only feat/block-2.5-control-plane
```

Fast-forward succeeded; no fallback path needed. Tag `v13-block-3-close` placed at `bed7d26`.

User-approval gate: explicit "approved, push direct" received before push. Direct push selected over PR flow per single-developer platform doctrine (`.pre-commit-config.yaml`: `# no-commit-to-branch omitted: single-developer platform commits on main`).

Push:
```
git push origin main                # 06c57d4..bed7d26  main -> main
git push origin v13-block-3-close   # * [new tag]   v13-block-3-close -> v13-block-3-close
```

Verification:
```
$ git ls-remote origin refs/heads/main
bed7d26e28ee56dddb40982cf5e8a0bfc20f73e0  refs/heads/main             ✅ matches local

$ git ls-remote origin refs/tags/v13-block-3-close
bed7d26e28ee56dddb40982cf5e8a0bfc20f73e0  refs/tags/v13-block-3-close ✅ tag landed

$ gh pr list --state open
(empty)                                                               ✅ no surprise PRs
```

Final main lineage:
```
bed7d26  Block 4.A: correct Block 3 P7 closeout falsifiable claim
232171b  Block 4.A registry reconciliation
45efc6d  Block 4.A doctrine refresh
a251161  Phase 13 Block 2.5: operator control plane
db55b02  Phase 13 Block 3: Display & Voice platform layer (P2–P7 close)
06c57d4  Phase 13 Block 3 Phase 1: Foundation audit (read-only)        ← prior main HEAD
```

### A7 — Final regression probe + this report

Probe: `bash docs/phase-13/h1-regression-probe.sh block-4a-final`.

```
Gate block-4a-final summary: PASS=15 FAIL=0 WARN=3
```

WARN breakdown:

| WARN entry | New? | Acceptable? | Source |
|---|---|---|---|
| `openhands.internal` not in macOS DNS cache | no | yes | informational; same as Block 2.5 Gate 5. Cold-cache miss when site not actively used. |
| `restic snapshot list inaccessible` (CLI/creds Vault-fetched) | no | yes | informational; same as Block 2.5 Gate 5. Restic creds are by design Vault-fetched only. |
| no gate-specific dependency probes defined for `block-4a-final` | no (gate-id-driven, not state-driven) | yes | informational; new gate ids without bespoke probes always emit this. Same shape as Block 2.5 Gate 2 / Gate 5 with their own gate ids. |

Container roster: 47 up, 0 restarting. Vault sealed=false; audit log capturing (size delta confirms live writes). Caddy + `.internal` reverse proxy: 4 of 5 sample sites returned 200/307 successfully. Cross-service deep probe (Nextcloud→Postgres) returned 200, DB reachable. Credential-shape heuristic on `/tmp`: clean.

**Zero new WARN entries; gate satisfied.**

## Hash-only credential verification

Per platform doctrine, no credential values displayed. Verification was hash/equality-only:

| Surface | Verification | Outcome |
|---|---|---|
| Vault audit log integrity | size delta during probe (4,635,849 → 4,639,185 bytes) | live writes confirmed |
| Vault seal status | `sys/seal-status` returned sealed=false | unsealed |
| Operator Argon2 hash | provision script's `vault kv get -field=argon2_hash secret/control-plane/operator` was a no-op (already set; sha256 prefix display only on first-write) | hash retained from Block 2.5 P2 |
| `secret/meross`, `secret/warmup` | `vault kv list` returned `No value found` | absent (matches A5 correction) |
| Sonarr/Radarr/Prowlarr API keys | not surfaced anywhere in 4.A's commits; pre-existing leak in service-registry.yaml is **explicitly out of scope**, deferred to a separate credential-remediation block per spec | unchanged |

## Deliverables — checklist

- [x] `main` fast-forwarded to include Block 2.5 + Block 3 + 4.A doctrine refresh + 4.A registry reconciliation + 4.A P7 correction
- [x] Tag `v13-block-3-close` at the merge boundary (`bed7d26`); pushed to origin
- [x] This closeout report (`docs/phase-13/PHASE_13_BLOCK_4A_CLOSEOUT_2026-04-29.md`)
- [x] `docs/PLATFORM_OVERVIEW.md` updated minimally (phase, services count, date)
- [x] `CLAUDE.md` "Current Phase" line updated; Platform Rules section untouched
- [x] ADR-A-007 collision resolved: bare A-007 → A-010; Syncthing keeps A-007; README index reflects both plus A-009
- [x] `service-registry.yaml` drift reduced from 5 unregistered (note: not 19 as the planning artifact stated; methodology variance documented above) to 0
- [x] Block 3 P7 closeout corrected (Meross/Warmup Vault paths)
- [x] Final regression probe PASS=15 FAIL=0 (no new WARN; 3 pre-existing acceptable WARN documented above)

## Post-Block-4.A follow-up list

Tracking carries forward from CLAUDE.md "Post-Block-2 Follow-up List". Per spec, A7 marks remaining items:

| Item | Disposition |
|---|---|
| Caddy dead-route prune (12 `.internal` routes) | **Deferred to Block 4.C.** 4.A intentionally does not touch Caddyfile so 4.B's discovery observes current state including dead routes. |
| Homepage widget completion (Grafana SA token, Uptime Kuma slug) | **Deferred to Block 4.C.** Not closed at Block 4.A close. |
| Block 3 — MacBook Pro M5 parity | Unchanged, future block. |
| Phase 14 — Loki for log-based per-site Caddy analysis | Unchanged, future block. |

## Out of scope for 4.A — confirmed not touched

- Caddy dead-route prune.
- Sonarr/Radarr API key rotation in `service-registry.yaml`.
- `iap-credential-rotate-trigger.sh` implementation.
- Restic test-restore (quarterly mandate).
- New tooling (NetBox, Structurizr, MkDocs).
- `ARCHITECTURE.md` creation (4.C work).
- `docs/roadmap/ITEMS/` reconciliation (4.B/4.C; Plane is canonical).

## Commits landed in 4.A

```
db55b02  Phase 13 Block 3: Display & Voice platform layer (P2–P7 close)   [pre-existing on branch]
a251161  Phase 13 Block 2.5: operator control plane                        [A2]
45efc6d  Block 4.A doctrine refresh                                        [A3]
232171b  Block 4.A registry reconciliation                                 [A4]
bed7d26  Block 4.A: correct Block 3 P7 closeout falsifiable claim          [A5]
```

The closeout commit for this report follows immediately per Commit-and-Push Doctrine.
