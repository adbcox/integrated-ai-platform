# RGC Operator Runbook

## Overview

Roadmap Governance Core (RGC) manages the lifecycle of roadmap items, CMDB entities, CMDB-to-roadmap links, feature-block packages, and integrity findings.

All pipeline steps are idempotent and safe to rerun.

## Database setup

```sh
export RGC_DATABASE_URL=sqlite:///rgc.db     # or a PostgreSQL URL
python3 bin/rgc.py roadmap sync --dry-run    # verify before first write
```

Tables are created automatically on first run via `Base.metadata.create_all`.

## Standard pipeline

Run in order. Each step depends on outputs from previous steps.

### Step 1 — Sync roadmap items

```sh
python3 bin/rgc.py roadmap sync
```

Reads `docs/roadmap/ROADMAP_INDEX.md` and all item YAML files. Upserts items into `roadmap_item`. Emits `duplicate_id` and `naming_violation` findings.

### Step 2 — Import CMDB entities

```sh
python3 bin/rgc.py cmdb import path/to/cmdb_seed.yaml
```

Validates and upserts entities from a YAML/JSON seed file. Emits `invalid_canonical_name`, `invalid_entity_type`, and `duplicate_canonical_name` findings.

Seed file format:
```yaml
entities:
  - canonical_name: prod.rgc.api
    display_name: RGC API
    entity_type: service
    environment: prod
    criticality: high
    owner: platform-team
```

### Step 3 — Refresh CMDB links

```sh
python3 bin/rgc.py links refresh
```

Matches roadmap item text against CMDB canonical names. Persists `exact_canonical` links (confidence=1.0). Emits `unresolved_cmdb_link` and `ambiguous_cmdb_link` findings.

### Step 4 — Run integrity review

```sh
python3 bin/rgc.py integrity run
```

Validates naming convention, priority, item_type, category, and near-duplicate titles. Writes timestamped artifact to `artifacts/governance/integrity/`.

### Step 5 — Refresh feature-block packages

```sh
python3 bin/rgc.py planner refresh
```

Groups roadmap items by category, scores each group, upserts `feature_block_package` records, and writes artifacts to `artifacts/governance/packages/`.

### Step 6 — Capture metrics

```sh
python3 bin/rgc.py metrics capture
```

Writes `metric_snapshot` rows for the global scope and each category scope.

## Querying findings

```sh
# All open findings
curl http://localhost:8000/integrity/findings?status=open

# Findings by type
curl http://localhost:8000/integrity/findings?finding_type=unresolved_cmdb_link

# Resolve a finding
curl -X PATCH http://localhost:8000/integrity/findings/<finding_id> \
  -H "Content-Type: application/json" \
  -d '{"status": "resolved", "resolution_note": "Manually verified; no CMDB entity required."}'
```

## Querying packages

```sh
curl http://localhost:8000/packages
curl http://localhost:8000/packages/PKG-PLATFORM
```

## Querying metrics

```sh
curl http://localhost:8000/metrics/scopes/global/global
curl http://localhost:8000/metrics/scopes/category/CORE
```

## Impact view for a roadmap item

```sh
curl http://localhost:8000/roadmap/items/RM-PLATFORM-001/impact
```

## Dry-run mode

Every pipeline command accepts `--dry-run`. In dry-run mode: findings are checked for existence (SELECT) but not persisted (no INSERT), links and packages are not written, artifacts are not written.

```sh
python3 bin/rgc.py roadmap sync --dry-run
python3 bin/rgc.py links refresh --dry-run
python3 bin/rgc.py planner refresh --dry-run
```

## Artifact locations

| Pipeline step | Artifact directory |
|---|---|
| Integrity review | `artifacts/governance/integrity/` |
| Package planner | `artifacts/governance/packages/` |

Each package artifact is `PKG-{CATEGORY}.json` containing the package metadata and member list.
