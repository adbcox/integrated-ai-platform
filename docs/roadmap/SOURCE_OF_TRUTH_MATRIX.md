# Roadmap Source of Truth Matrix

## Purpose

This matrix defines which roadmap or adjacent document controls which class of planning truth.

## Matrix

| Truth type | Primary authority | Secondary/reference surfaces | Notes |
|---|---|---|---|
| Architecture direction | `docs/architecture/MASTER_SYSTEM_ARCHITECTURE.md` | architecture support docs | Roadmap is downstream of architecture |
| Roadmap status truth | `ROADMAP_STATUS_SYNC.md` | `ROADMAP_AUTHORITY.md` | Use for open/completed/archived truth |
| Roadmap strategic interpretation | `ROADMAP_MASTER.md` | `ARCHITECTURE_ALIGNMENT.md` | Summary and priority reading, not direct status truth |
| Backlog inventory | `ROADMAP_INDEX.md` | per-item files | Inventory view only |
| Standards and schema | `STANDARDS.md` | template files | IDs, metrics, readiness, intake rules |
| Grouped execution logic | `FEATURE_BLOCK_GROUPING.md` | per-item grouping notes | Used for package/block planning |
| External system catalog | `EXTERNAL_APPLICATIONS_AND_INTEGRATIONS.md` | crosswalk doc | Catalog and posture, not status truth |
| Execution readiness gate | `EXECUTION_READINESS_CHECKLIST.md` | execution packs | Determines readiness discipline |
| Dependency and blocker handling | `DEPENDENCY_MANAGEMENT.md` | item dependency sections | For planning and sequencing |
| Risk and issue handling | `RISK_AND_ISSUE_MANAGEMENT.md` | item risk notes | For escalation and tracking discipline |

## Reader rule

When two documents appear to conflict, determine what kind of truth is being asked for and follow the matching primary authority in this matrix.
