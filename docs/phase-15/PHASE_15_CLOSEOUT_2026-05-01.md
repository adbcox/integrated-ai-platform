# Phase 15 Closeout — 2026-05-01

**Phase:** 15 — Vault Recovery + Information Architecture Hygiene
**Opened:** 2026-04-30
**Closed:** 2026-05-01
**Tag:** phase-15-final
**Closeout commit:** (this commit)

---

## Charter

Phase 15 was opened on 2026-04-30 to address two streams of work originally:

1. Recovery from the Vault cascade incident (Sev-2, 2026-04-30) — KV mount data loss + seal-vault data volume destruction during a 9-hour autonomous-debug window
2. Mac Studio M3 Ultra Day-1 integration — physical arrival expected 2026-05-01, with a prepared execution script and 3 pre-actions

On 2026-05-01 the operator selected Path C (defer Mac Studio Day-1, prioritize documentation system completeness + audit closure first), shifting Phase 15 closeout scope from Day-1 integration to audit-driven cleanup of the items raised in `docs/phase-15/COMPREHENSIVE_AUDIT_2026-05-01.md` (committed 3105f07).

The audit same-week fix list (R-01 through R-08) plus information-architecture hygiene (S9-F1 through S9-F4) plus a doctrine-level deliverable (PROJECT_FRAMEWORK.md, D-15-10) plus Path B resolution of the ADR-A-007 dirty edit (D-15-07) together formed the closing scope.

## Deliverables closed

| ID | Title | Status | Closing commit / state |
|---|---|---|---|
| D-15-01 | Audit + validation pass committed | DONE | 3105f07 |
| D-15-02 | Information architecture hygiene | DONE | 6a18e6c, 818ab3e, 2ce52d8, 3631b62, c2cc83d, a9d4129 (last task closed via D-15-07) |
| D-15-03 | Backup chain repair (R-01) | DONE | bb5d315 (policy) + Vault state (AppRole + policy re-provisioned) + crontab fix + MinIO `backup-bucket-rw` policy + dedicated backup user + fresh Restic repo + baseline snapshot `784ff718` |
| D-15-04 | Vault audit device re-enable (R-02) | DONE | Vault config; audit log writing to `/vault/logs/audit.log` |
| D-15-05 | PreToolUse hooks (R-03) | DONE | 3cc764b |
| D-15-06 | vault-test instance (R-08) | DONE | a8f3abe |
| D-15-07 | ADR-A-007 dirty edit (Path B) | DONE | 9d50f84 |
| D-15-10 | PROJECT_FRAMEWORK.md doctrine | DONE | e7d1c5b |
| D-15-09 | Phase 15 closeout (this doc) | DONE | (this commit) |

## Deliverable deferred

| ID | Title | Status | Reason |
|---|---|---|---|
| D-15-08 | Loose-doc retirement (`/Users/adriancox/`) | DEFERRED to Phase 16 | Operator instruction (2026-05-01): no MacBook filesystem changes this session |

## Discoveries handled this session (not separate deliverables)

- **MinIO bucket versioning enabled** on `qnap/backups` — was off; accidental delete protection now in place. Found during D-15-03 testing.
- **Strava cron entries fixed** — `refresh-strava-token.sh` and `sync-strava-to-calendar.py` had the same `/var/log` unwritable redirect issue as R-01; both were silently failing. In-place crontab fix, no commit (crontab is not repo-tracked).
- **Stale `~/vault-init-keys.txt` renamed** to `~/vault-init-keys.txt.PRE-KV-LOSS-INVALID-20260430` per audit XF-5.

## Carry-overs to Phase 16

Beyond D-15-08, the following items were identified during Phase 15 and are not blocking for closure but should appear in the Phase 16 charter:

- **Mac Studio Day-1 execution** — 3 pre-actions still apply: Vault audit re-enable (now done per D-15-04, one less), Headscale `homelab` user decision, NetBox+Zabbix Vault token path verification under their actual field names
- **Block 4.D retroactive closeout** — InvenTree is deployed (4 containers running, AppRoles provisioned) but lacks the formal closeout suite that Block 4.A and 4.C have
- **Block 4.E cross-index service** — STRUCTURAL BLOCKER for autonomous coding, the operator stated meta-goal. The validator exists at `scripts/cross-index-validate.py` (Phase 14 D-XINDEX); the queryable HTTP/MCP service does not. Without this, an agent must search NetBox + InvenTree + Plane + ADRs + runbooks + vault paths separately — which is precisely the gap that caused the audit Section 3 service-removal claims to be wrong on every named service
- **Vault data volume in Restic backup** — `scripts/backup.sh` includes `/var/lib/docker/volumes/vault_vault-data/_data` only when readable by `admin`; it is not (root-owned in Colima). Right fix is `vault operator raft snapshot save` integration, not raw volume read. Estimated ~1h to design and integrate
- **Recovery-handoff doctrine update** — add a value-correctness verification requirement (not just leaf-path-population count) based on the `secret/minio/backup` finding during D-15-03 (where the rebuild populated bogus values that nothing caught until Restic auth failed)
- **Documentation drift detection automation** — pre-commit hooks for ADR governance violations (in-place edits to Accepted ADRs), CI checks for broken doc pointers in CLAUDE.md, ADR README index sync. Most of the manual hygiene work D-15-02 caught could be detected automatically going forward

## Lessons learned

1. **47/47 paths populated does not equal 47/47 values correct.** The post-cascade KV rebuild on 2026-04-30 verified leaf paths existed; it did not verify their values matched what consumers expected. The bogus 11-character MinIO access key in `secret/minio/backup` only surfaced when Restic auth retried with exponential backoff during D-15-03 testing. Recovery-handoff doctrine should be amended to require value-correctness probes (use these creds end-to-end against the live target) not just population counts.

2. **The audit Section 3 service-removal claims were wrong on every named service.** Homarr, docker-socket-proxy-control, sportarr, upgrade-receiver/watcher, AnythingLLM all had documented roles in operator architectural decisions captured in past planning chats (April 25-28) that the audit did not cross-reference. The morning planning chat (a856b02c) cargo-culted the audit removals into a destructive execution prompt that would have rolled back Phase 14 deliverables; the operator caught it before forwarding. The cross-reference gap motivates Block 4.E (cross-index service) as the real enabler for autonomous coding — an agent needs a unified queryable surface or it will keep producing wrong recommendations from partial sources.

3. **Operator-side gates (PreToolUse hooks) are needed to make autonomous execution survivable.** Even when planning produces a reasonable-looking prompt, conversation-history search can return stale or pre-investigation recommendations as if they were current decisions. Hooks make the execution layer fail-closed against the worst classes of commands regardless of what the planner produced.

4. **Multi-window file-transfer friction matters.** Early in this session the control window was producing files for the operator to download from chat and SCP to Mac Mini — operator pushed back as excessive ceremony. Switching to direct SSH placement was significantly faster and lower-cognitive-load. The operating model doctrine should reflect this: control window writes operational artifacts directly via SSH; only repo commits route through the execution window for git-hook compliance.

## Phase 16 charter draft

Proposed scope (operator confirms at Phase 16 open):

- D-16-01 Block 4.D retroactive closeout (InvenTree)
- D-16-02 Block 4.E cross-index service design + initial implementation — the autonomous-coding structural enabler
- D-16-03 Mac Studio Day-1 execution (with the 2 remaining pre-actions: Headscale homelab user, NetBox+Zabbix Vault token path verify)
- D-16-04 Vault data volume in backup chain (operator raft snapshot integration)
- D-16-05 Loose-doc retirement (deferred from D-15-08)
- D-16-06 Documentation drift detection automation (CI/pre-commit checks)
- D-16-07 Recovery-handoff doctrine update (value-correctness verification)

## References

- `docs/phase-15/COMPREHENSIVE_AUDIT_2026-05-01.md` — Phase 15 audit (immutable historical artifact, 3105f07)
- `docs/phase-15/COMPREHENSIVE_AUDIT_VALIDATION_2026-05-01.md` — validation companion (immutable historical artifact, 3105f07)
- `docs/phase-15/PHASE_15_RECOVERY_HANDOFF_2026-04-30.md` — cascade incident recovery doctrine
- `docs/phase-15/PHASE_15_KV_LOSS_2026-04-30.md` — KV-loss postmortem
- `docs/phase-15/PHASE_15_VAULT_API_ADDR_NETWORK_INCIDENT_2026-04-30.md` — api_addr network misdiagnosis postmortem
- `docs/phase-15/PHASE_15_VAULT_AUDIT_HANDOFF_2026-04-30.md` — vault audit handoff during cascade
- `docs/PROJECT_FRAMEWORK.md` — PMP+ITIL framework, Phase 15 table updated to reflect closure
- `docs/PHASE_LOG.md` — Phase 15 entry updated to COMPLETE
