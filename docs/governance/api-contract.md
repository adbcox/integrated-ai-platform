# RGC API Contract

Base URL: `http://<host>:8000`

All responses are JSON. Timestamps are ISO 8601 UTC.

---

## Health

### `GET /health`

Returns `{"status": "ok"}`. Used by load balancers and health checks.

---

## Pipeline triggers

### `POST /sync/roadmap`

Trigger a roadmap sync from source files.

Query parameters:
- `dry_run` (bool, default `false`)

Response:
```json
{"items_created": 2, "items_updated": 0, "items_unchanged": 5, "findings_created": 1}
```

### `POST /reviews/integrity`

Trigger an on-demand integrity review.

Query parameters:
- `dry_run` (bool, default `false`)

Response:
```json
{"items_checked": 7, "findings_created": 2, "findings_skipped": 0, "artifact_path": "artifacts/governance/integrity/integrity_review_20260420T120000Z.json"}
```

---

## Roadmap items

### `GET /roadmap/items`

List all roadmap items.

Query parameters:
- `status` (optional): filter by status string
- `category` (optional): filter by category token

Response: array of `RoadmapItemResponse`

```json
[
  {
    "id": "RM-CORE-001",
    "title": "...",
    "category": "CORE",
    "item_type": "capability",
    "priority": "P1",
    "status": "planned",
    "description": null,
    "source_path": "docs/roadmap/ROADMAP_INDEX.md",
    "source_hash": "abc123",
    "naming_version": "1.0",
    "created_at": "2026-04-20T12:00:00Z",
    "updated_at": "2026-04-20T12:00:00Z"
  }
]
```

### `GET /roadmap/items/{item_id}`

Get a single roadmap item by ID. Returns `404` if not found.

### `GET /roadmap/items/{item_id}/impact`

Return impact view for a roadmap item: the item plus all persisted CMDB links.

Response: `RoadmapImpactResponse`

```json
{
  "roadmap_id": "RM-CORE-001",
  "title": "...",
  "links": [
    {
      "entity_id": "uuid",
      "link_type": "exact_canonical",
      "confidence": 1.0,
      "evidence_ref": "canonical_name:prod.rgc.api",
      "canonical_name": "prod.rgc.api",
      "display_name": "RGC API",
      "entity_type": "service",
      "created_at": "...",
      "updated_at": "..."
    }
  ]
}
```

Returns `404` if the item does not exist.

### `GET /roadmap/links`

List persisted roadmap-to-CMDB links.

Query parameters:
- `roadmap_id` (optional): filter by roadmap item ID

Response: array of `RoadmapLinkResponse`

---

## Integrity findings

### `GET /integrity/findings`

List integrity findings.

Query parameters:
- `status` (optional): `open` | `resolved` | `accepted` | `suppressed`
- `finding_type` (optional): e.g. `unresolved_cmdb_link`, `invalid_category`

Response: array of `IntegrityFindingResponse`

### `GET /integrity/findings/{finding_id}`

Get a single finding. Returns `404` if not found.

### `PATCH /integrity/findings/{finding_id}`

Transition finding lifecycle.

Request body:
```json
{
  "status": "resolved",
  "resolution_note": "Optional explanation."
}
```

Valid status values: `resolved` | `accepted` | `suppressed`

Returns updated `IntegrityFindingResponse`.

---

## CMDB entities

### `GET /cmdb/entities`

List CMDB entities.

Query parameters:
- `entity_type` (optional)
- `environment` (optional)

### `GET /cmdb/entities/{entity_id}`

Get a single CMDB entity. Returns `404` if not found.

---

## Feature-block packages

### `POST /planner/packages/refresh`

Run the package planner: group roadmap items by category, score, upsert packages.

Query parameters:
- `dry_run` (bool, default `false`): evaluate without persisting

Response:
```json
{
  "packages_created": 2,
  "packages_updated": 0,
  "packages_unchanged": 0,
  "members_added": 7,
  "artifact_paths": ["artifacts/governance/packages/PKG-CORE.json"]
}
```

### `GET /packages`

List all feature-block packages ordered by score descending.

Query parameters:
- `scope` (optional): filter by category scope

Response: array of `FeatureBlockPackageResponse` (includes `members` array)

```json
[
  {
    "package_id": "PKG-CORE",
    "title": "Core Feature Block",
    "scope": "CORE",
    "status": "draft",
    "score": 0.857,
    "rationale": "3 item(s); 2 with CMDB links; 0 open finding(s); score=0.857",
    "artifact_path": "artifacts/governance/packages/PKG-CORE.json",
    "created_at": "...",
    "updated_at": "...",
    "members": [
      {"roadmap_id": "RM-CORE-001", "member_role": "primary", "added_at": "..."}
    ]
  }
]
```

### `GET /packages/{package_id}`

Get a single package with members. Returns `404` if not found.

---

## Metrics

### `POST /metrics/capture`

Capture a metrics snapshot for all scopes (global + each category).

Query parameters:
- `dry_run` (bool, default `false`)

Response:
```json
{
  "snapshots_written": 3,
  "scopes_captured": ["global:global", "category:CORE", "category:OPS"]
}
```

### `GET /metrics/scopes/{scope_type}/{scope_ref}`

Return the most-recent metric snapshot for a scope.

Path parameters:
- `scope_type`: `global` | `category` | `package`
- `scope_ref`: e.g. `global`, `CORE`, `PKG-CORE`

Returns `404` if no snapshot exists for this scope.

Response: `MetricSnapshotResponse`

```json
{
  "snapshot_id": "uuid",
  "scope_type": "global",
  "scope_ref": "global",
  "metrics": {
    "item_count": 12,
    "items_by_status": {"planned": 8, "in_progress": 4},
    "items_by_category": {"CORE": 5, "OPS": 7},
    "link_coverage_pct": 58.33,
    "open_finding_count": 3,
    "package_count": 2
  },
  "captured_at": "2026-04-20T12:00:00Z"
}
```

---

## HTTP status codes

| Code | Meaning |
|---|---|
| 200 | Success |
| 404 | Resource not found |
| 422 | Validation error (invalid request body) |
