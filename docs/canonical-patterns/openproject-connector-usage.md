# Canonical Pattern — OpenProject Connector Usage

**Module:** `framework/openproject_connector.py`
**Status:** Authoritative as of D-17-04 WP-17-04-04 (2026-05-02)
**Replaces:** `plane-connector-usage.md` (Plane CE retired in WP-17-04-06)

This document is the canonical usage pattern for the OpenProject API
connector. New consumers MUST follow it. The connector intentionally
mirrors the Plane connector's call signatures (Phase 13 Increment 1
patterns) so the migration cost was minimised.

The patterns below are not stylistic preferences — every one of them
maps to a specific OpenProject API behavior discovered in WP-17-04-04
authoring.

## 1. Always import `RateLimitError` alongside `OpenProjectAPI`

```python
from framework.openproject_connector import OpenProjectAPI, RateLimitError
```

OpenProject is permissive (~100 req/sec) and rate-limiting is off by
default, but the symbol exists and downstream code that catches a broad
`except Exception` before catching `RateLimitError` will swallow the
intended-narrow failure mode. Carrying the import keeps call sites
robust if rate-limiting is ever enabled.

## 2. Auth is HTTP basic with `apikey:<token>`

Not Bearer, not query-param. The connector handles this internally via
`requests.Session.auth`; never construct headers by hand.

The token at `secret/openproject/api#token` is **iap-sync's token**
post-WP-17-04-04. Admin tokens are destroyed by the mint script, so any
script that needs admin operations (e.g., creating custom fields) must
use the Rails runner (see `openproject-bootstrap-ext-id-field.sh` for
the canonical pattern).

## 3. External ID is the canonical lookup key

```python
api.get_issue_by_external_id("D-16-04")  # → WP dict or None
api.get_module_by_external_id("Phase-16")  # → Version dict or None
```

OpenProject Versions don't natively support external_id; the connector
encodes it as the version name itself. WorkPackages use a custom field
(id 2, name "External ID"). Legacy `Plane RM ID` (CF id 1) is preserved
for read-only fallback on the 670 imported WPs but is no longer written
by new code.

## 4. Status discovery hits `/api/v3/statuses` directly

Not the form schema. The form schema's `status.allowedValues` is
filtered to the *current WP's permissible transitions* under the
caller's role workflows — on a create form, that returns just `[New]`.

For the canonical Plane-shaped status list, call:

```python
states = api.ensure_states()
# {"Backlog": 1, "In Progress": 7, "Done": 12, "Cancelled": 14, "On hold": 13}
```

The keys are Plane-era state names mapped onto OpenProject status IDs;
the connector handles the mapping so call sites don't need to know
OpenProject's status vocabulary.

## 5. Always pass `lockVersion` on PATCH

The connector's `update_issue` and `add_issues_to_module` re-fetch the
WP first to get its current `lockVersion`, then send it on the PATCH.
Skipping this returns HTTP 409 Conflict. Don't construct PATCH payloads
manually — go through the connector.

## 6. Description format is **markdown**, not HTML

```python
api.create_issue(
    name="...",
    description="<p>Some <strong>HTML</strong></p>",  # connector strips/converts
    ...
)
```

The connector's `_strip_tags` converts the small HTML envelope produced
by sync code (`<p>`, `<strong>`, `<code>`) to markdown before PATCH.
OpenProject stores markdown and renders HTML on read with `op-uc-*`
class wrappers — diff on `description.raw`, not `description.html`,
or you'll see perpetual drift.

## 7. Project module gating

WorkPackage permission checks return false if the
`work_package_tracking` module is not enabled on the project, *even if
the role grants the permission*. The mint script enables it. If you're
testing the connector against a fresh project, run the mint script
first or enable manually:

```ruby
proj.enabled_module_names = ["work_package_tracking"]
proj.save!
```

## 8. Workflow gating

The role must have at least one Workflow row to receive *any* status
information from the API — `/api/v3/statuses` returns 403 for a role
with zero workflow rows. Status transitions on PATCH are also workflow-
gated. The mint script clones Member's workflows AND adds explicit
`*→{New, In progress, Closed, On hold, Rejected}` for every type so the
sync can land WPs in any of those terminal statuses from any starting
point.

## 9. Pagination via offset (1-based)

```python
data = api._get(api._url("/work_packages"), params={
    "filters": "...", "pageSize": 200, "offset": 1
})
```

Continue while `offset * page_size < data["total"]`. The connector's
`list_all_issues` does this internally; reach for the raw paginator
only if you need a non-default filter.

## 10. Categories ≠ Plane Labels (1-to-1, not 1-to-many)

OpenProject WorkPackages have **one** category, not many. The connector
maps Plane's `label_ids` parameter to the *first* label only and uses
it as the WP's category. If a Plane consumer relied on multi-label
semantics, that semantics is lost on the OpenProject side — surface
this in the call site rather than masking it.

## 11. Versions are project-scoped

Versions live under a project; you can't create a Version that spans
projects. The connector's `ensure_module(external_id, name, ...)`
collapses `external_id` to `name` (because Versions lack a native
external_id field) and creates the Version under the bound project.

---

## Migration mapping (Plane → OpenProject)

| Plane concept       | OpenProject equivalent | Notes                              |
|---------------------|------------------------|-------------------------------------|
| Workspace           | (no analog)            | OpenProject is single-tenant        |
| Project             | Project                | identifier == Plane's project slug  |
| Issue               | WorkPackage            | external_id via custom field        |
| Module              | Version                | external_id encoded as Version name |
| Label               | Category               | 1:1; multi-label collapses to first |
| State               | Status                 | system-wide, mapped via ensure_states |
| API token           | API token              | per-user, single key, reset to rotate |
| description (HTML)  | description (markdown) | connector converts on write         |
