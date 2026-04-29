# Canonical Pattern — Plane Connector Usage

**Module:** `framework/plane_connector.py`
**Status:** Authoritative as of Phase 13 Increment 1 (2026-04-29)
**Replaces:** Ad-hoc Plane API access scattered across `bin/` scripts.

This document is the canonical usage pattern for the Plane API
connector. New consumers MUST follow it. Existing consumers were
audited and brought into compliance in Phase 13 Increment 1
(commit `1eed06c`).

The patterns below are not stylistic preferences — every one of them
maps to a specific bug or near-miss documented in Block 4.C C6
discoveries (#14 pagination terminator, #15 broad-except rate-limit
masking, #16 wire-format silent drop).

## 1. Always import `RateLimitError` alongside `PlaneAPI`

```python
from framework.plane_connector import PlaneAPI, RateLimitError
```

The connector raises `RateLimitError` (not a generic `HTTPError`) on
HTTP 429. This is intentional — callers MUST distinguish a rate-limit
event from an item-level error so the back-off response is
load-bearing rather than buried.

## 2. Catch `RateLimitError` BEFORE `except Exception`

The single most expensive bug class in the connector consumer
inventory was a broad `except Exception` masking a `RateLimitError`,
causing the consumer to record the 429 as an item-level failure and
move on. By the time it surfaced, the rate budget was burned for the
minute and dozens of items had been mis-classified.

```python
try:
    issue, created = api.upsert_issue(
        external_id = "RM-API-100",
        title       = "Add rate limiting",
        description = "...",
        state_name  = "Accepted",
        category    = "API",
        priority    = "Medium",
    )
except RateLimitError as exc:
    # explicit handling: back off, retry budget, surface to operator
    print(f"  RATE-LIMIT: {exc} — sleeping 60s", file=sys.stderr)
    time.sleep(60)
    return "rate_limited"
except Exception as exc:
    # only genuine item-level errors reach here
    print(f"  ERROR: {exc}", file=sys.stderr)
    return "error"
```

The order matters: `RateLimitError` first, then `Exception`. The
opposite order does not type-check the way you might expect — a
parent-class catch in front of a child-class catch is unreachable
in Python and silently swallows the 429.

For the canonical retry loop with bounded budget, see
`scripts/backfill-plane-labels.py::_with_429_retry`.

## 3. Bulk operations: pace the writes

Plane's V1 API enforces a **60 requests per minute** rate limit per
API token. This includes GETs. Practical pacing rules:

- **Writes (POST/PATCH):** Bulk writers should sleep ~1.5 seconds
  between writes (`time.sleep(1.5)` in `bin/configure_plane_agile.py`).
- **GET-then-PATCH workflows:** Each item costs 2× the budget.
  `upsert_issue` GETs the existing-issue lookup before PATCHing —
  ~120 items/minute is the ceiling, not 60.
- **Bulk fetches:** `list_all_issues()` paginates internally. Don't
  call it twice per operation — `tool_get_stats` was previously
  doing this and consuming 2× the rate budget for one
  user-visible result.

## 4. First-batch verify: trust but verify the wire format

After any change to the wire format (new field, new schema, new key),
re-read the FIRST mutation of the new flow before issuing a batch.
This guards against the Discovery #16 worst-case: a PATCH that returns
200 but silently dropped the field because the wire-format key was
wrong. Plane V1 silently ignores unknown keys.

The connector exposes `verify_issue_field(issue_id, field, expected)`
for exactly this purpose:

```python
issue, created = api.upsert_issue(...)
if created and not self._first_create_verified and item.get("category"):
    expected_label = api.ensure_label(item["category"])
    if not api.verify_issue_field(issue["id"], "labels", [expected_label]):
        raise SystemExit(2)  # abort the batch — labels are not landing
    self._first_create_verified = True
```

The verify happens once per batch, not per item. The cost is one
extra GET on the first item; the protection is catching a silent
wire-format regression before consuming the full rate budget.

`verify_issue_field` compares lists order-insensitively (`labels`
ordering is not stable on Plane) and scalar fields by `==`.

## 5. Bulk-create patterns

Two helpers for label management exist and have different shapes:

- `ensure_label(name)` — single label, requires a list-fetch round
  trip on first call (cached for 5 minutes thereafter). Use for
  one-off creates.
- `ensure_labels_bulk([names])` — multi-label. Issues one
  `list_labels()` GET, then creates the missing ones with 1.1s
  pacing between writes. Use whenever you have ≥3 labels to ensure.

State management is similarly bulk-aware via `ensure_states()`.

## 6. Pagination — terminate on `next_page_results`, not `next_cursor`

The connector handles this correctly inside `list_issues()`, but
**custom pagination loops outside the connector must do the same**.
Plane V1 returns a non-null `next_cursor` even past the end of the
dataset (it's an incrementing offset, not a sentinel). The
authoritative terminator is:

```python
done = (
    data.get("next_page_results") is False
    or data.get("count") == 0
    or not data.get("results")
)
```

This is Discovery #14. Don't roll your own pagination — call
`list_all_issues()` if you need everything, or `list_issues(cursor=...)`
in a loop if you need to stream-process.

## 7. Use the connector's high-level helpers, not raw HTTP

| Use case                          | Helper                              |
| --------------------------------- | ----------------------------------- |
| Create or update by external ID   | `upsert_issue(...)`                 |
| Rich description with sections    | `create_enhanced_issue(...)`        |
| Just change status                | `update_issue_state(id, name)`      |
| Search / lookup                   | `search_issues(query)`              |
| Lookup by RM-* ID                 | `get_issue_by_external_id(id)`     |
| Fast counts (no full enumeration) | `get_stats_fast()`                  |
| Verify a mutation landed          | `verify_issue_field(id, k, v)`     |

The internal `_get`/`_post`/`_patch` methods are not part of the
public API — they exist for consumers that need access to endpoints
the high-level helpers don't yet cover (e.g., cycles, modules in
`bin/configure_plane_agile.py`). New endpoints reached through these
should be promoted to typed helpers as they stabilise.

## 8. Wire format reference

These are the exact JSON keys Plane V1 expects on the wire. The
connector handles them correctly; this section exists so a consumer
debugging an HTTP 200 with no apparent effect can sanity-check.

**Issue create (POST `/issues/`):**
- `name`               (string, required)
- `description_html`   (string, optional — wrap plain text in `<p>...</p>`)
- `state`              (UUID, optional — state ID, NOT name)
- `priority`           (string: `"urgent" | "high" | "medium" | "low" | "none"`)
- `labels`             (list of UUIDs — **NOT `label_ids`**)
- `assignees`          (list of UUIDs)

**Issue update (PATCH `/issues/{id}/`):**
- Same keys as create. **`labels` (NOT `label_ids`)** — same trap.
- Wrong keys are silently ignored. 200 OK, no error, no effect.

The `label_ids` mistake is so easy to make that the connector's
Python kwarg is also called `label_ids` (it serializes to `labels`
inside the connector). New code should never see the string
`"label_ids"` as a JSON key. If you do, that's a bug.

## 9. Adding a new consumer — checklist

Before merging a new script that calls Plane:

- [ ] Imports `RateLimitError` and catches it explicitly before any
  broad `except Exception`.
- [ ] Uses high-level helpers (§7) rather than raw `_get`/`_post`.
- [ ] If it's a writer: paces writes (~1.5s between mutations) and
  performs first-batch verify (§4) on novel flows.
- [ ] If it's a reader: tolerates `RateLimitError` cleanly (skip the
  cycle, surface to operator, etc.) — does not crash a watch loop.
- [ ] Has at least one wire-format test in
  `tests/integration/plane_connector/` if it introduces a new
  payload shape.
- [ ] Tested against a real Plane instance for the first run; only
  rely on mocks for regression.

## 10. References

- `framework/plane_connector.py` — the connector itself.
- `tests/integration/plane_connector/test_wire_format.py` —
  HTTP-layer regression tests.
- `scripts/backfill-plane-labels.py` — reference implementation of
  the bounded retry pattern (`_with_429_retry`).
- `docs/phase-13/INCREMENT_1_DCN_AUDIT_2026-04-29.md` — Phase 13
  Increment 1 audit findings (F1–F11).
- Block 4.C C6 closeout report — original C6 follow-up list (#10–#15)
  that this work resolves.
- ADR-A-011 — IV&V loop pattern.
- ADR-A-013 — folded gates doctrine.
