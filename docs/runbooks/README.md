# Runbooks Index

Operator-facing table of contents for `docs/runbooks/`.

Status legend:
- `canonical` — active doctrine/runbook for current operations
- `superseded` — replaced by newer runbook; kept for migration/historical reference
- `stale-candidate-tracked-by-D-17-71` — active but under ongoing drift-hardening pass

## Platform Operations

| Runbook | Description | Status |
|---|---|---|
| `add-new-service.md` | Canonical service onboarding with Vault Agent sidecar pattern | stale-candidate-tracked-by-D-17-71 |
| `add-new-host.md` | Host onboarding (CMDB, DNS, monitoring, Caddy integration) | stale-candidate-tracked-by-D-17-71 |
| `restart-services.md` | Service restart procedures across platform stacks | stale-candidate-tracked-by-D-17-71 |
| `incident-response.md` | Incident triage/escalation procedure | canonical |
| `operating-model.md` | IV&V/folded-gate execution doctrine | stale-candidate-tracked-by-D-17-71 |
| `what-changed-last-24h.md` | Rapid 24h change-surface investigation commands | stale-candidate-tracked-by-D-17-71 |
| `remote-work-recovery.md` | Remote-operations recovery flow | canonical |
| `singapore-pre-departure-checklist.md` | Pre-travel unattended-ops checklist | canonical |
| `foundation-install-status-track-2.md` | Foundation install status — Track 2 (install-time platform state) | canonical |
| `home-transition-mac-studio.md` | Home-transition runbook: control-center workload shift onto Mac Studio | canonical |
| `mac-studio-day-1.md` | Mac Studio Day-1 bring-up checklist (D-17-15 substrate) | canonical |

## Drift / Governance / PM Sync

| Runbook | Description | Status |
|---|---|---|
| `drift-detection.md` | Canonical drift-detection framework and hooks | stale-candidate-tracked-by-D-17-71 |
| `drift-detection-procedure.md` | Operational drift audit procedure (container/CMDB/Vault/Caddy) | stale-candidate-tracked-by-D-17-71 |
| `openproject-sync-and-enrich.md` | Canonical OpenProject sync + enrichment doctrine | canonical |
| `openproject-sync.md` | OpenProject sync runbook (baseline sync path) | canonical |
| `plane-sync.md` | Retired Plane sync reference | superseded |
| `plane-web-auth.md` | Retired Plane web-auth issue note | superseded |
| `scripts-inventory.md` | Operator-facing scripts inventory and dependency map | canonical |
| `xindex.md` | Cross-index / reference index (general) | canonical |
| `xindex-mcp.md` | Cross-index focused on MCP surfaces | canonical |
| `regression-probe-failure.md` | Regression-probe failure triage (drift-detection family) | canonical |

## DNS / Network / Access

| Runbook | Description | Status |
|---|---|---|
| `opnsense-add-host-overrides.md` | Add/verify OPNsense Dnsmasq host overrides | canonical |
| `opnsense-dhcp-dns-push.md` | Push internal DNS via OPNsense DHCP | canonical |
| `headscale-client-onboarding.md` | Headscale client enrollment flow | canonical |
| `macbook-headscale-enrollment.md` | MacBook-specific Headscale enrollment | canonical |
| `macos-firewall-homebrew-binaries.md` | macOS firewall/local-network behavior for brew binaries | canonical |
| `remote-sudo-scripts.md` | Canonical SSH+sudo terminal-allocation pattern | canonical |
| `caddy-internal-ca-trust.md` | Caddy internal-CA trust distribution (operator-installable; D-17-115) | canonical |

## Launchd / Scheduling

| Runbook | Description | Status |
|---|---|---|
| `launchd-jobs-canonical.md` | Canonical post-D-17-51 LaunchDaemon authoring/deploy pattern | canonical |
| `launchd-jobs.md` | Launchd scheduled jobs operations and recency checks | canonical |

## Vault / Credentials / Recovery

| Runbook | Description | Status |
|---|---|---|
| `vault-approle-provision-canonical.md` | Canonical Vault AppRole provisioning pattern | canonical |
| `rotate-credentials.md` | Credential rotation workflow via Vault | stale-candidate-tracked-by-D-17-71 |
| `vault-token-rotation.md` | Vault token rotation specifics | canonical |
| `vault-unseal.md` | Vault unseal procedure | canonical |
| `vault-rekey.md` | Vault rekey procedure | canonical |
| `vault-recovery-from-shamir.md` | Vault recovery path for Shamir-related incidents | canonical |
| `vault-restore-from-backup.md` | Vault restore from backups | canonical |
| `vault-test-instance.md` | Vault test-instance operations | canonical |
| `H1-rollback.md` | H1 rollback procedure | canonical |

## Arr / Media / NAS

| Runbook | Description | Status |
|---|---|---|
| `arr-stack-add-component.md` | Add new component to arr stack | canonical |
| `qnap-downloads-mount.md` | QNAP SMB mount workflow for arr imports | stale-candidate-tracked-by-D-17-71 |
| `syncthing-rebuild.md` | Syncthing rebuild/recovery operations | canonical |
| `retire-service.md` | Canonical service retirement/decommission runbook | canonical |
| `nextcloud-caldav.md` | Nextcloud CalDAV integration notes | canonical |
| `buildarr-excluded-services.md` | Buildarr config-as-code exclusions (Sonarr v4, Sportarr; F11 worked example) | canonical |
| `download-pipeline-troubleshooting.md` | Download pipeline triage (Prowlarr → arr → seedbox) | canonical |

## AI / Local Models / Tooling

| Runbook | Description | Status |
|---|---|---|
| `goose-operations.md` | Goose execution-surface operations | canonical |
| `pull-new-model.md` | Model pull/provenance workflow | canonical |
| `capability-discovery.md` | Capability discovery diagnostic flow | canonical |
| `exo-cluster-operations.md` | exo cluster operations and constraints | canonical |
| `observability-doctrine.md` | Observability doctrine and layering | canonical |
| `pretooluse-hooks.md` | pre-tool-use hooks behavior and safeguards | canonical |
| `git-autopush-hook.md` | post-commit auto-push install and fail-soft audit behavior | canonical |
| `migrate-source-of-truth.md` | Source-of-truth migration procedure | canonical |
| `aider-default-workflow.md` | Aider default-workflow runbook (local coding-task surface) | canonical |
| `serena-mcp-integration.md` | Serena MCP integration runbook (semantic-code MCP surface) | canonical |
| `track-1a-litellm-status.md` | Track 1A LiteLLM proxy status reference | canonical |

## Legacy Monitoring

| Runbook | Description | Status |
|---|---|---|
| `zabbix-operations.md` | Zabbix operations reference (legacy monitoring path) | superseded |
| `zabbix-templates.md` | Zabbix template authoring/import reference | canonical |
| `zabbix-trapper-pattern.md` | Zabbix trapper pattern (collector → trapper item; D-17-105 reference) | canonical |

---

## Legacy-reference scan

Per D-17-62 scope, this index also catalogues classes of legacy references retained intentionally inside the runbook set. These are not drift — they are load-bearing historical citations that future drift sweeps should preserve.

**Class 1 — `docs/_retired/` pointers.** `retire-service.md` and `buildarr-excluded-services.md` reference retired-service exhibits (worked-example posture). Retained: legitimate historical citation; do not rewrite to canonical paths.

**Class 2 — sportarr restoration-context references.** Eight files (Vault policy paths, restart procedures, retirement record + reversal record at `docs/_retired/sportarr-2026-05-01.md`, and runbook citations) keep the sportarr name as the worked example for retirement-record-as-restoration-playbook substrate (Finding 10 / F10). Retained: doctrine substrate.

**Class 3 — CR-17-NNN-escalated deliverable IDs.** `aider-default-workflow.md` cites D-17-94/95/96/97/101/103/111 (escalated via CR-17-001); `pull-new-model.md` cites D-17-104; `zabbix-trapper-pattern.md` cites D-17-105. CR-17-NNN escalation to Phase 18 does not invalidate the deliverable IDs themselves — the runbook references remain accurate as historical anchors. Retained: legitimate ID continuity.

## Maintenance posture

- **Append-on-author rule.** New runbooks must be indexed in the appropriate category table at authoring time; absence from this index is the canonical drift signal D-17-62 surfaced.
- **Quarterly drift sweep.** D-17-71 is the umbrella deliverable for stale-candidate aging-out + index re-baselining. Index entries flagged `stale-candidate-tracked-by-D-17-71` are eligible for review during each sweep window.
- **Status legend stability.** The three-status legend (`canonical` / `superseded` / `stale-candidate-tracked-by-D-17-71`) is intentionally narrow; status promotions/demotions are doctrine-bearing changes and should be committed as their own atom rather than bundled with index additions.
