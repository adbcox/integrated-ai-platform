# Plane sync from PROJECT_FRAMEWORK.md — Runbook (RETIRED)

**Status:** RETIRED 2026-05-01 with Plane CE itself, in D-17-04 WP-17-04-06.
**Replaced by:** [`openproject-sync.md`](openproject-sync.md)

The Plane connector and sync script are kept in-tree as historical reference
(`framework/plane_connector.py`, `scripts/plane-sync-from-framework.py`)
through the active D-17 phase only and will be moved under `_retired/` in a
later cleanup pass. Do not invoke them.

For the current PROJECT_FRAMEWORK.md → PM substrate sync, see
[`openproject-sync.md`](openproject-sync.md).

Historical context (Plane-era):

- Doctrine that originated here (ADR-A-006: repo-owned docs canonical, PM
  is operational overlay; one-way write only) has been carried forward
  unchanged.
- Status mapping that originated here has been reified into
  `framework/openproject_connector.MARKDOWN_TO_OP_STATUS`.
- Markdown parser regexes (`ROW_RE`, `PHASE_HEADING_RE`) are reused
  verbatim by `scripts/openproject-sync-from-framework.py`.
