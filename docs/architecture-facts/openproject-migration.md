# OpenProject migration — durable findings

Chronicle of non-obvious facts learned while standing up OpenProject as
the platform's PM substrate (D-17-04 onwards) and during the D-17-31
roadmap-sync extension. Items here outlast any single deliverable; new
findings append to the bottom with date + originating WP.

---

## Finding 1 — OpenProject API v3 uses flat collections + `_links`, NOT nested resource paths

**Date:** 2026-05-03
**Originating WP:** D-17-31 WP-04 (operator chronicle ask)
**Severity:** Medium (API contract; affects anything writing to OP)

### What
OpenProject's REST API v3 (stable since 2015, current at time of writing)
exposes most write-side associations as **root collections** that take a
`_links.<parent>` reference, not as project-nested sub-resources.

Concretely, two endpoints we hit during D-17-31 returned 404 when called
project-nested:

| Wrong (project-nested)                  | Right (root + `_links`)                            |
|------------------------------------------|----------------------------------------------------|
| `POST /api/v3/projects/{id}/versions`    | `POST /api/v3/versions` with `_links.definingProject` |
| `POST /api/v3/projects/{id}/categories`  | *(N/A — categories are read-only over the API)*    |

Categories specifically are surfaced read-only by API v3 — they must be
created via the OpenProject web UI or settings; no `POST` /
`PATCH` / `DELETE` exists.

### Why it bit us
The `framework/openproject_connector.py` code originally constructed
`_proj_url("/versions")` for `create_module()` and a similar
project-nested `POST` for `ensure_label()`. Both raised
`TypeError: 'NoneType' object is not subscriptable` downstream because
the 404 response body was empty and the code assumed a created object
back. Three hours of debugging Phase-18 version creation traced to the
endpoint shape, not auth, not project ID, not payload.

### Origin hypothesis (carry-over from Plane)
The connector predates the Plane → OpenProject migration. Plane uses
deeply nested resource paths
(`/api/v1/workspaces/<wsid>/projects/<pid>/issues/`,
`/api/v1/workspaces/<wsid>/projects/<pid>/modules/`, etc.), where almost
every write has its parent IDs in the URL. When the connector was
retargeted to OpenProject, the issue/work-package endpoints got
flattened correctly, but the lower-traffic association endpoints
(versions, categories) were left in their Plane-shaped form. They never
fired in production until D-17-31 needed to auto-create a Phase-18
version, exposing the latent bug.

### Doctrine takeaway
**Before adding any new write endpoint to a connector for OpenProject:**
1. Check the official endpoint reference at
   <https://www.openproject.org/docs/api/endpoints/>.
2. Default assumption: associations are root collections that take a
   `_links.<parent>` href in the body, NOT project-nested sub-paths.
3. If the OpenProject UI exposes a setting that the API does not (e.g.
   categories, project types, custom-field definitions), assume that
   surface is API-read-only and raise a typed exception in the
   connector rather than crashing on an empty response body.

### Files touched by the fix
- `framework/openproject_connector.py` — `create_module()` rewritten to
  use `_url("/versions")` + `_links.definingProject`; `ensure_label()`
  rewritten to raise `CategoryNotFoundError` instead of
  attempting an impossible `POST`.
- `scripts/openproject-sync-from-framework.py` — uses `get_category_id`
  (lookup-only) with description-text fallback when category absent.

### Verification record
- Root `POST /api/v3/versions` with `_links.definingProject` returned a
  201-equivalent body with the new version object — confirmed via
  Phase-18 backfill 2026-05-03.
- All other connector write endpoints audited against the API v3 docs
  during D-17-31 WP-05 — no other carry-over patterns found. The bug
  was localized to two endpoints.

---
