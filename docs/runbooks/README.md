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

## DNS / Network / Access

| Runbook | Description | Status |
|---|---|---|
| `opnsense-add-host-overrides.md` | Add/verify OPNsense Dnsmasq host overrides | canonical |
| `opnsense-dhcp-dns-push.md` | Push internal DNS via OPNsense DHCP | canonical |
| `headscale-client-onboarding.md` | Headscale client enrollment flow | canonical |
| `macbook-headscale-enrollment.md` | MacBook-specific Headscale enrollment | canonical |
| `macos-firewall-homebrew-binaries.md` | macOS firewall/local-network behavior for brew binaries | canonical |
| `remote-sudo-scripts.md` | Canonical SSH+sudo terminal-allocation pattern | canonical |

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

## Legacy Monitoring

| Runbook | Description | Status |
|---|---|---|
| `zabbix-operations.md` | Zabbix operations reference (legacy monitoring path) | superseded |
