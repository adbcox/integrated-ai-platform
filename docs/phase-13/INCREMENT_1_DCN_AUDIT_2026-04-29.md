# Increment 1 D-CN — Plane connector + consumers audit

**Date:** 2026-04-29
**Scope:** `framework/plane_connector.py` + 6 consumers (per Appendix C
A-2 decision: all 6, not just the 3 named in C6 #10).
**Gate type:** Full IV&V audit (the connector hardening work has not
been audited against this specific contract before — see ADR-A-013
"no novel surface" condition fails).
**Audit checks:** pagination contract; `RateLimitError` vs broad
`Exception`; 2× rate-budget consumption (GET-then-PATCH or similar);
payload key correctness (`labels` not `label_ids`); first-batch verify
presence; error class hierarchy / catch order.

---

## 1. Connector itself — `framework/plane_connector.py`

### 1.1 Pagination termination contract — fixed (Discovery #14)

**Lines 277-310 (`list_issues`)**: Already patched in commit
`651f2f3` to honour `next_page_results=False` / `count=0` /
`not results` as the terminator, falling back to `next_cursor` for
other endpoints. **Status: OK; tests pending.**

### 1.2 `create_issue` payload key bug — UNFIXED, parallel to Discovery #16

**Line 360**: `payload["label_ids"] = label_ids`. Plane V1 PATCH
silently ignores unknown keys (Discovery #16). The same is true on
POST: `create_issue` is silently dropping labels at create time.

**Blast radius:** every issue created via `create_issue()` since
the line landed has had its labels silently dropped. Discovery #16's
parallel-bug section calls this out explicitly. R-6 in the campaign
plan documents this as "live breakage today, not a hypothetical
future risk."

**Fix:** `payload["label_ids"]` → `payload["labels"]` at line 360.
**This is the load-bearing fix for Phase C** (the back-fill cannot
run until this lands).

### 1.3 `upsert_issue` — secondary instance of the same bug

**Line 470**: `updates["label_ids"] = [label_id]` in the existing-
issue update path of `upsert_issue`. Same silent-no-op trap as
Discovery #16 — Plane V1 PATCH expects `labels`, not `label_ids`.

**Blast radius:** every roadmap sync that re-syncs an existing
issue calls `update_issue(existing["id"], updates)` with this
malformed key. Existing issues are *not* re-labeled — the labels
field is silently ignored. The 4.C C4 back-fill landed labels
correctly via `scripts/backfill-plane-labels.py` (which uses the
correct `labels` key directly, not via `upsert_issue`).
**Updates via `bin/sync_roadmap_to_plane.py` against existing
issues have been silently dropping label updates.**

**Note:** for *new* issues, line 480 of `upsert_issue` calls
`create_issue(..., label_ids=[label_id])` which then triggers
the line-360 bug. The two bugs are linked: a single roadmap-sync
pass through `upsert_issue` triggers either line 360 (create
path) or line 470 (update path), and both silently drop labels.

**Fix:** `updates["label_ids"]` → `updates["labels"]` at line 470.

### 1.4 `RateLimitError` class hierarchy

**Line 17**: `class RateLimitError(Exception)`. `RateLimitError`
inherits from base `Exception`, which makes it easy for caller
code to mask under a broad `except Exception` handler (Discovery
#15 Bug 2). The C6 follow-up #11 names two remediation options:
reparent away from `Exception`, or document explicit catch-order.

**Recommendation: document, do not reparent.** Reparenting
breaks every existing caller's broad `except Exception:` block,
which is too disruptive a change for a doctrine-level fix.
Documentation + the canonical-pattern README (B.4) is the
proportionate fix.

**Fix:** add a docstring warning on the class definition; cite the
C6 #11 follow-up; reference the canonical-pattern doc.

### 1.5 First-batch verify helper

The connector has no first-batch-verify primitive. Discovery #15
codified the pattern (re-GET issue #1 after first PATCH; assert
mutation took; abort run if it didn't). The pattern is currently
implemented inline at consumer level (or not at all).

**Fix:** add `verify_issue_field(issue_id, field, expected_value)`
helper to the connector. Returns `True` if the field's current
value contains/equals the expected value, `False` otherwise.
Consumers can call this after their first batch of writes to
implement the doctrine.

### 1.6 Other audit checks — no findings

- `_request` method correctly raises `RateLimitError` on 429 (line
  138) without sleeping. Pacing is delegated to the caller. ✅
- `list_labels`, `list_states`, `list_workspaces` are paginated-
  but-cached (3xx-line range). They use `result.get("results",
  result)` defensively which is fine for non-paginated endpoints.
  No 2× consumption pattern.
- `_get`/`_post`/`_patch`/`_delete` are bare wrappers. No payload-
  shape concerns at this layer.

---

## 2. Consumer — `bin/configure_plane_agile.py`

| Check | Status | Evidence |
|---|---|---|
| Pagination | N/A | Doesn't paginate; uses `list_states(use_cache=False)` and `list_labels(use_cache=False)` which return single-page results. |
| `RateLimitError` handling | **WARN — masked** | Lines 144, 165, 191-192, 216 catch broad `except Exception as e:` and print + continue. `RateLimitError` is silently logged and the next iteration proceeds — but the script does `time.sleep(1.5)` between cycle/module creates and (on cycle path) `time.sleep(3)` on exception. The 60/min budget is respected, but a 429 could happen on a parallel run with another consumer. |
| 2× rate consumption | OK | Each create operation = 1 POST; no GET-then-write pattern. |
| Payload key | OK | Uses `create_state` and `create_label` (which take `name`/`color`/`group` — Plane native field names). Cycle/module creation uses `project_id` (line 250, 258) — Plane serializer requires that exact key per the inline comment. |
| First-batch verify | N/A | Idempotent skip-if-exists path at lines 136, 156, 182, 206 reads existing names before creating. Sufficient for this consumer's shape. |

**Recommended fix:** wrap the broad `except Exception` blocks at
lines 144, 165, 191, 216 with explicit `except RateLimitError`
first, plus a backoff. Severity: minor — this consumer runs only
during initial Plane configuration (not in steady state) and is
typically operator-triggered.

---

## 3. Consumer — `bin/ai_requirement_translator.py`

| Check | Status | Evidence |
|---|---|---|
| Pagination | N/A | No pagination. |
| `RateLimitError` handling | OK (delegated) | Calls `api.upsert_issue(...)` which routes through the connector. Errors propagate. The CLI wrapper doesn't trap them. |
| 2× rate consumption | **NOTE** | `upsert_issue` does a `get_issue_by_external_id` (1 GET) + either `update_issue` (1 PATCH) or `create_issue` (1 POST). Per item: 2 requests. At 1.1 sec spacing in `ensure_labels_bulk` etc. the budget holds; for single-shot calls from this CLI the budget is fine. **No fix needed for this consumer.** |
| Payload key | **CRITICAL — inherits bug** | Line 247 calls `upsert_issue` which itself has the `label_ids` bug at lines 470/480. Fixing the connector fixes this consumer transparently. |
| First-batch verify | N/A | Operator-driven CLI, single-issue use case. |

**Recommended fix:** none direct; bugs land via connector fix.

---

## 4. Consumer — `bin/sync_roadmap_to_plane.py`

**This is the principal consumer affected by Discovery #16's
parallel bug.** Roadmap-sync is what populates Plane from
`docs/roadmap/ITEMS/*.md`, and it has been silently dropping
labels on both create (via `create_issue`) and update (via
`upsert_issue`'s update path) since the connector landed.

| Check | Status | Evidence |
|---|---|---|
| Pagination | N/A | Reads from local markdown, writes to Plane. |
| `RateLimitError` handling | **WARN — masked** | Line 213-215 catches broad `except Exception as exc:`, prints + returns "error". `RateLimitError` will be silently counted as `errors += 1` rather than triggering backoff. The script continues at full pace. |
| 2× rate consumption | **WARN** | Same as 3 above — `upsert_issue` is 2 reqs/item. The script has only `time.sleep(0.15)` every 10 items (line 240), which is `0.015 s/item` of pacing. With 2 reqs/item at no per-request pacing, sustained throughput depends on Plane's response time alone. **In practice the script has been running fine** because Plane response times are ~150-250ms each, so 2 reqs/item ≈ 0.4 sec/item ≈ 150/min — over budget. The script is implicitly throttled by Plane's 429 responses, which it counts as errors. |
| Payload key | **CRITICAL — inherits bug** | Line 204 `api.upsert_issue(...)`. This is *the* call that makes Phase C necessary. |
| First-batch verify | **MISSING** | No re-read after the first batch. The Discovery #16 silent-no-op cost the C4 back-fill ~10 minutes of wasted writes; this script has been silently dropping labels on every sync run. |

**Recommended fixes:**
1. (CRITICAL, lands via connector) Connector fix at lines 360 and 470 transparently fixes this consumer.
2. (Tightening) Wrap the broad `except Exception` at line 213 with explicit `except RateLimitError` first; on `RateLimitError`, sleep `BACKOFF_429`-equivalent and retry.
3. (First-batch verify) After the first `upsert_issue` call, re-GET the issue, assert that labels include the category. Abort the run if not.

---

## 5. Consumer — `bin/sync_plane_to_markdown.py`

| Check | Status | Evidence |
|---|---|---|
| Pagination | OK (delegated) | `list_all_issues()` on line 100 routes through the connector's now-correct pagination (post-Discovery #14). |
| `RateLimitError` handling | **WARN — unmasked** | Lines 81-82 catch only `subprocess.CalledProcessError` for git ops. The Plane calls (`list_all_issues`, `list_states`) propagate `RateLimitError` unhandled. The script crashes on 429 without backoff. |
| 2× rate consumption | OK | Reads only — `list_all_issues` and one `list_states`. No write-amplification. |
| Payload key | N/A | No PATCH/POST — read-only sync direction. |
| First-batch verify | N/A | Read-only. |

**Recommended fix:** wrap the Plane calls in a `try/except
RateLimitError` with backoff retry. Severity: medium — script
runs in `--watch` mode, so a single 429 shouldn't kill the
poll loop.

---

## 6. Consumer — `scripts/backfill-plane-labels.py`

| Check | Status | Evidence |
|---|---|---|
| Pagination | OK | Lines 132-143 paginate via `api.list_issues(cursor=c, ...)`, terminating on null cursor (the connector handles `next_page_results=False` internally per the Discovery #14 fix). |
| `RateLimitError` handling | **OK** | Line 111-121 has a `_with_429_retry` helper that catches `RateLimitError` explicitly with bounded retries and `BACKOFF_429` sleep. Line 270-280 has explicit `RateLimitError` catch *before* the broad `except Exception`. **This is the model for what other consumers should do.** |
| 2× rate consumption | **OK** | Line 252-267: removed pre-fetch GET (Discovery #15 fix); apply loop is 1 PATCH per issue. |
| Payload key | **OK** | Line 267: `api.update_issue(issue_id, {"labels": new_labels})`. Uses correct `labels` key directly (Discovery #16 fix). |
| First-batch verify | **MISSING** | The script's verification was done via post-run independent re-read at the gate close (which is what surfaced Discovery #16 in the first place). It's not in the script itself. C6 #15 is exactly this gap. |

**Recommended fix:**
- **First-batch verify in-script.** After the first 1-3 successful
  PATCHes (depending on how the script defines "first batch"),
  re-GET those issues and assert the labels were applied. Abort
  if not. This is the codification of the doctrine that surfaced
  Discovery #16.

---

## 7. Consumer — `mcp/plane_mcp_server.py`

| Check | Status | Evidence |
|---|---|---|
| Pagination | OK (delegated) | Uses `list_all_issues()` (line 259, 390) which routes through the connector's now-correct pagination. |
| `RateLimitError` handling | **WARN — masked** | Line 488-492 in the MCP server's `tools/call` handler catches broad `except Exception as exc:` and returns the error to the MCP client. `RateLimitError` will land in the MCP response as `Error: 429 on ...` rather than triggering backoff. **For an LLM-facing MCP server this is acceptable** — the LLM caller can choose to retry. But it's worth documenting that the MCP server is rate-budget-passive (does not back off itself). |
| 2× rate consumption | **NOTE** | `tool_get_issue` (line 279) calls `get_issue_by_external_id` (1 GET via search) — single read. `tool_update_status` (line 331) calls `get_issue_by_external_id` (1 GET) + `update_issue_state` which itself calls `get_state_id` (cached) + `update_issue` (1 PATCH) = 2 reqs/call. `tool_get_stats` (line 386) calls `get_stats()` which calls `list_states` + `list_all_issues` (paginated, ~7 GETs for 600+ issues) + then `list_all_issues` again at line 390 — that's two full `list_all_issues` calls, ~14 paginated GETs in one stats request. **`tool_get_stats` doubles the read budget.** |
| Payload key | **CRITICAL — inherits bug** | Line 314 `api.upsert_issue` (lands via connector fix). Line 345 `api.update_issue_state` which uses `update_issue` with `{"state": sid}` — `state` is the correct Plane V1 key for the state field, not `state_id`. ✅ for state path. |
| First-batch verify | N/A (LLM-facing) | Operator/LLM is responsible for verifying mutations through subsequent tool calls. |

**Recommended fixes:**
1. (CRITICAL, lands via connector) Connector fix at lines 360 and 470.
2. (Performance) `tool_get_stats` calls `list_all_issues()` twice (once via `get_stats()`, once directly at line 390). Refactor to call once. Severity: minor — only matters for the rare `get_stats` tool call.
3. (Doc) Note in the MCP server's docstring that it is rate-budget-passive: a 429 from Plane returns to the MCP client as an error; the LLM caller is expected to retry.

---

## 8. Summary findings table

| # | Component | Issue | Severity | Fix location |
|---|---|---|---|---|
| F1 | `framework/plane_connector.py:360` | `create_issue` builds `payload["label_ids"]` — silently dropped by Plane V1 | **CRITICAL** | Connector — load-bearing for Phase C |
| F2 | `framework/plane_connector.py:470` | `upsert_issue` (update path) builds `updates["label_ids"]` — same silent-drop | **CRITICAL** | Connector |
| F3 | `framework/plane_connector.py:17` | `RateLimitError(Exception)` — easy to mask under broad catch | Medium | Docstring + canonical-pattern doc |
| F4 | `framework/plane_connector.py` | No `verify_issue_field` first-batch-verify helper | Medium | Add helper |
| F5 | `bin/sync_roadmap_to_plane.py:213` | Broad `except Exception` masks `RateLimitError` on every item | Medium | Add explicit catch + backoff |
| F6 | `bin/sync_roadmap_to_plane.py` | No first-batch verify after first `upsert_issue` | Medium | Add re-read assertion |
| F7 | `bin/sync_plane_to_markdown.py:100,101` | `list_all_issues` / `list_states` not wrapped for `RateLimitError` | Medium | Wrap with backoff |
| F8 | `scripts/backfill-plane-labels.py` | No in-script first-batch verify (the C4 case that surfaced #16) | Medium | Add re-read after first 1-3 PATCHes |
| F9 | `bin/configure_plane_agile.py:144,165,191,216` | Broad `except Exception` masks `RateLimitError` | Low | Add explicit catch (operator-triggered, low-frequency) |
| F10 | `mcp/plane_mcp_server.py:386-403` | `tool_get_stats` calls `list_all_issues` twice | Low | Refactor to single call |
| F11 | `mcp/plane_mcp_server.py` (doc) | MCP server is rate-budget-passive; not documented | Low | Docstring note |

**No findings beyond the C6 #10–#15 scope** that require new
work outside the planned increment. All 11 fixes are addressable
within the D-CN sub-phase B.2 budget. **No scope expansion needed.**

---

## 9. C6 follow-up cross-reference

| C6 # | Topic | Audit fix(es) addressing it |
|---|---|---|
| 10 | Audit consumers for rate-limit handling | F5, F7, F9 (and F11 docstring) |
| 11 | Audit error class hierarchy | F3 (docstring), and B.4 canonical-pattern doc |
| 12 | Pagination termination contract README | B.4 canonical-pattern doc |
| 13 | Dry-run coverage gap (apply path) | B.3 integration tests |
| 14 | `create_issue` builder fix | F1 + F2 (parallel bug) |
| 15 | First-batch verify pattern | F4 (helper), F6, F8 (in-script applications), B.4 doc |

All six C6 items addressed by the fixes named in §8.

---

## 10. Audit gate — recommendation

**Recommendation: proceed to B.2 execution.** The audit surfaced
exactly the scope anticipated in the campaign plan (six C6 items
plus the parallel `upsert_issue` bug at line 470 which is a
direct consequence of Discovery #16's lesson). No novel surface
requiring scope expansion. No consumer is fundamentally broken in
a way unrelated to the C6 follow-ups.

The execution plan for B.2 will:

1. Apply F1 + F2 connector fixes (single commit — they are the
   same bug at two sites).
2. Apply F3 docstring on `RateLimitError`.
3. Apply F4 `verify_issue_field` helper.
4. Apply F5–F11 per-consumer fixes (folded per ADR-A-013 once the
   first consumer's fix lands cleanly — they are mechanical
   applications of the same pattern: explicit `except RateLimitError`
   before broad catch).

Stop-and-surface conditions for B.2:

- Connector fix breaks `bin/sync_roadmap_to_plane.py` regression
  (full sync after the fix lands).
- Per-consumer fix surfaces a new behaviour not anticipated here.
- B.3 integration tests reveal a class of bugs not caught by this
  audit.
