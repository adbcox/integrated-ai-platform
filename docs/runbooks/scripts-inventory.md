# Scripts Inventory + Dependency Map (D-17-63)

Last audited: 2026-05-04
Scope: `scripts/` recursive (`.sh`, `.py`)
Total scripts: 78

## 1) Canonical entrypoints (operator-facing)

| Script | Purpose | Invoked by | Key deps |
|---|---|---|---|
| `scripts/roadmap-create.sh` | Deliverable intake/close-out flow | manual | `artifact-ingest.sh`, `openproject-sync-from-framework.py` |
| `scripts/check-repo-coherence.py` | Repo drift/coherence checks | pre-commit, manual | `opnsense_client.py`, `phase-deliverable-count.py` |
| `scripts/platform-registry/refresh.sh` | Refresh runtime inventory registry | launchd, manual | `platform-registry/lib/registry_writer.py`, `refresh-artifacts.sh` |
| `scripts/buildarr-run.sh` | Buildarr apply/check run | launchd, manual | Vault env + Buildarr runtime |
| `scripts/arr-apikey-sweep.sh` | Prowlarr/consumer functional probe/resync | launchd, manual | Prowlarr/Sonarr/Radarr APIs |
| `scripts/backup.sh` | Restic nightly backup | launchd | `vault-snapshot-warm.sh` |

## 2) Provisioning scripts

| Script family | Purpose | Shared dependency |
|---|---|---|
| `scripts/provision-*.sh` | Vault policy/AppRole bootstrap per service | `scripts/lib/vault-admin-token.sh` |
| notable scripts | `provision-buildarr.sh`, `provision-bazarr.sh`, `provision-scraparr.sh`, `provision-cleanuparr.sh`, `provision-netbox.sh`, `provision-inventree.sh`, `provision-control-plane.sh` | same |

## 3) OpenProject/PM scripts

| Script | Role | Status |
|---|---|---|
| `openproject-sync-from-framework.py` | Canonical markdown->OpenProject sync | canonical |
| `openproject-enrich-from-framework.py` | Metadata enrichment pass | canonical |
| `openproject-bootstrap-enrichment-fields.sh` | Field bootstrap helper | canonical |
| `openproject-bootstrap-ext-id-field.sh` | External ID field bootstrap | canonical |
| `openproject-import-from-plane.py` | Plane snapshot importer | legacy/orphan-candidate |

## 4) CMDB/NetBox scripts

| Script | Role |
|---|---|
| `cmdb_source.py` | CMDB source loader (`yaml`/`netbox`) |
| `validate-cmdb.sh` | Runtime CMDB validation |
| `cmdb-equivalence.sh` | YAML vs NetBox equivalence check |
| `migrate-registry-to-netbox.py` | One-time migration utility |
| `netbox-*` scripts | NetBox field/tag/service registration helpers |

## 5) Launchd-related scripts

| Script | Role | Current posture |
|---|---|---|
| `d-17-51-migrate-to-launchdaemons.sh` | LaunchAgent->LaunchDaemon migration | canonical |
| `d-17-51-verify-launchdaemons.sh` | daemon status/heartbeat verify | canonical |
| `d-17-51-launchagents-bootstrap-user-domain.sh` | user-domain bootstrap path | legacy empirical-failed branch |
| `d-17-51-launchagents-verify.sh` | user-domain verification helper | legacy branch support |
| `install-ollama-launchdaemon-mac-studio.sh` | remote LaunchDaemon install | canonical (`ssh -t` pattern) |

## 6) Artifact/model utilities

- `artifact-ingest.sh`, `artifact-resolve.sh` (D-17-37 substrate)
- `verify-model-provenance.sh`, `ollama-pull-verified.sh`, `hf-download-verified.sh`

## 7) Dependency map (text)

- `roadmap-create.sh` -> `artifact-ingest.sh` + `openproject-sync-from-framework.py`
- `platform-registry/refresh.sh` -> `platform-registry/lib/registry_writer.py` + `refresh-artifacts.sh`
- `backup.sh` -> `vault-snapshot-warm.sh`
- `buildarr-run.sh` -> Buildarr runtime + Vault-rendered env
- `provision-*.sh` -> `lib/vault-admin-token.sh`
- `check-repo-coherence.py` -> `opnsense_client.py` + local policy maps

## 8) Orphan/stale candidates (catalog only, no deletion)

- `scripts/cleanup_docker.sh`
- `scripts/openproject-import-from-plane.py`
- `scripts/platform-registry/install-launchd.sh`
- `scripts/provision-openproject.sh`
- `scripts/troubleshoot/troubleshoot.sh`
- `scripts/goose/goose-via-litellm-historical.sh` (explicit historical)
- Plane-era utilities retained for historical/migration context:
  - `plane-sync-from-framework.py`
  - `plane-final-snapshot.sh`
  - `plane-backfill-adr-stubs.py`
  - `backfill-plane-labels.py`
  - `curate-plane-backlog.py`

## 9) Legacy-reference findings (scripts scope only; catalog)

- `service-registry.yaml.DEPRECATED` without `.DEPRECATED`:
  - `scripts/migrate-registry-to-netbox.py` docstring reference
- Legacy user-domain LaunchAgent path:
  - `scripts/d-17-51-launchagents-bootstrap-user-domain.sh`
  - `scripts/d-17-51-launchagents-verify.sh`
  - `scripts/platform-registry/install-launchd.sh` (`~/Library/LaunchAgents`)
- Unbound legacy labels/aliases still present for compatibility:
  - `scripts/check-repo-coherence.py` (`caddy-unbound-parity` deprecated alias)
  - `scripts/d-17-51-*verify*.sh` includes `com.iap.caddy-unbound-parity` heartbeat compatibility
- Plane legacy scripts remain in-tree as historical/migration surfaces:
  - `scripts/plane-*`, `scripts/openproject-import-from-plane.py`, `scripts/backfill-plane-labels.py`, `scripts/curate-plane-backlog.py`
- `home.internal` and `Mac Mini M5` string drift:
  - no direct script occurrences in this audit.

## 10) Backlog notes (not acted in D-17-63)

1. Decide retention policy for Plane-era scripts (`_retired/scripts/` move vs keep in place with stronger headers).
2. Normalize remaining `service-registry.yaml.DEPRECATED` mentions to `.DEPRECATED` where scripts are still active.
3. Mark `d-17-51-launchagents-*` scripts as explicitly failed-branch artifacts in headers to prevent accidental reuse.
4. Reconcile `scripts/platform-registry/install-launchd.sh` (LaunchAgents installer) with post-D-17-51 LaunchDaemon doctrine, or retire it.
5. Evaluate whether `scripts/provision-openproject.sh` is orphaned/superseded by current token/bootstrap flow.
