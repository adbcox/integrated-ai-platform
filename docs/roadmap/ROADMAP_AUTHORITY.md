# Roadmap Authority Model

## Three-Layer Architecture

The roadmap system is deliberately structured into three layers, each with explicit authority and responsibilities:

### Layer 1: Canonical Item-State Layer (Authoritative)

**Location**: `docs/roadmap/items/RM-*.yaml`  
**Authority**: This is the source of truth. All status, archive status, and operational state must be tracked here.  
**Content**: Each roadmap item as a machine-readable YAML file with:
- Status (complete/completed/archived)
- Archive status (not_archived/ready_for_archive/archived)
- Archive readiness block with archived_at timestamp
- AI-operability fields (objective, scope, allowed_files, forbidden_files, validation_order, rollback_rule, artifact_outputs)
- Execution evidence and validation artifacts

**Responsibility**: Engineers and AI agents update item files directly when:
- Item work begins (status → in_progress if tracked)
- Item work completes (status → completed)
- Item is archived (archive_status → archived, archive_readiness.archived_at timestamp added)

### Layer 2: Derived Planning and Dependency Layer (Secondary)

**Location**: 
- `governance/roadmap_dependency_graph.v1.yaml` (dependency structure, blocking analysis)
- `artifacts/planning/next_pull.json` (next pull candidates, eligible items)

**Authority**: Derived from Layer 1. Must be kept in sync via tooling or manual audit.  
**Content**: 
- Dependency edges between items
- Blocking analysis sections (eligible_items, conditionally_eligible, blocked_items, archived_items)
- Next-pull ranking and candidates
- Planning state

**Responsibility**: Updated by:
- Manual synchronization audit when Layer 1 changes
- Automated validation to detect drift
- Explicit update when dependency structure changes (requires governance change)

### Layer 3: Derived Human-Visible Summary Layer (Tertiary)

**Location**:
- `docs/roadmap/ROADMAP_MASTER.md` (human-readable execution summary)
- `docs/roadmap/ROADMAP_INDEX.md` (human-readable item catalog)

**Authority**: Derived from Layer 1. Must reflect canonical state.  
**Content**: 
- High-level narrative descriptions
- Grouping and categorization
- Archived vs. active item listings
- Phase and priority summaries

**Responsibility**: Updated by:
- Manual curation when Layer 1 status changes
- Clear labeling that content is derived, not canonical
- Links back to item files for definitive status

## Authority Rules

1. **Single Source of Truth**: Item files (Layer 1) are authoritative. If Layer 2 or Layer 3 contradicts an item file, the item file is correct.

2. **Sync Discipline**: When an item file status or archive status changes:
   - Update Layer 2 files (dependency graph, next_pull.json) within the same session or explicitly track drift
   - Update Layer 3 files (ROADMAP_MASTER.md, ROADMAP_INDEX.md) to reflect the new status
   - Do not allow completed/archived items to appear in "active" sections

3. **No Split Authority**: Never create contradictions where:
   - An item is marked completed/archived in the item file but listed as active in summary docs
   - An item has different status in the item file vs. the dependency graph
   - The next_pull.json lists an archived item as eligible or in next_pull_candidates

4. **Explicit Derivation**: Layer 2 and Layer 3 documents must clearly state they are derived views and direct readers to item files for definitive status.

5. **Validation**: Run `bin/validate_roadmap_consistency.py` to detect and report contradictions between layers.

## Status Lifecycle

Items progress through these states:

```
in_progress (or untracked for simple items)
    ↓
completed (final state)
    ↓
archived (admin state, not active for execution)
```

**Archive Status** tracks when completed items are formally archived:
- `ready_for_archive`: Completed and ready to move to archive
- `archived`: Formally archived with timestamp

**Visibility Rules**:
- `in_progress` items may appear in planning and summary docs
- `completed` items still appear in active sections if execution is ongoing
- `archived` items must NEVER appear in "active" or "next" sections
- Archived items must be moved to separate "archived" sections in summary docs

## Detecting Drift

Check for these anti-patterns:
1. Item file has `archive_status: archived` but appears in ROADMAP_MASTER "Next active initiatives"
2. Item file has `status: completed` but appears in next_pull.json as `eligible_items`
3. Dependency graph has item with `status: archived` in `eligible_items` section
4. Item file has newer `updated_at` than the last Layer 2/Layer 3 update

Use `bin/validate_roadmap_consistency.py` to detect these automatically.

## Change Protocol

When updating roadmap status:

1. Update the item file (Layer 1): Change status and archive_status fields, add archived_at timestamp if archiving
2. Update the dependency graph (Layer 2): Move item from eligible_items to archived_items if applicable
3. Update next_pull.json (Layer 2): Remove item from candidates/nodes, add to archived_items if applicable
4. Update summary docs (Layer 3): Move item from active sections to archived sections
5. Run validation: `python bin/validate_roadmap_consistency.py` to confirm no drift
6. Commit all changes together with clear message: "Archive RM-XXXX: move to archived state across all layers"

## Governed Autonomous Pull Eligibility

`bin/compute_next_pull.py` is the canonical selector for autonomous pull readiness.

It computes candidates directly from Layer 1 item files and enforces:

- item is not archived and not `ready_for_archive`
- item status is plannable (not `complete`/`completed`)
- all hard dependencies (`depends_on`) are in terminal completion status
- bounded execution shape exists in `ai_operability`:
  - `allowed_files`
  - `forbidden_files`
  - `validation_order`
  - `rollback_rule`
  - `artifact_outputs`
- placeholder state conflicts are blocked (`status` plannable while execution + validation are terminal)

Blocked placeholder items must remain ineligible until canonical item status is reconciled.

## Operational Sovereignty Truth Surface

Local execution sovereignty for routine roadmap implementation is tracked separately from item status in:

- `governance/local_execution_sovereignty_status.v1.yaml` (authoritative verdict surface)
- `artifacts/autonomy/local_execution_sovereignty_verdict.json` (machine-readable evidence)

If these surfaces report `verdict: NO`, roadmap summaries must not claim routine local execution sovereignty.
