# Definition of Done

## Purpose

This document defines what "done" means for roadmap items in the Integrated AI Platform. Work is only complete when all these criteria are met.

## Artifact Completeness

Every completed item must produce:

- Machine-readable item file (RM-*.yaml in docs/roadmap/items/)
- Supporting schema files (governance/ or schemas/)
- Validation artifacts (tests, checks, proof files)
- Integration evidence (artifacts/, ADRs, documentation)
- Roadmap surface updates (ROADMAP_STATUS_SYNC.md, ROADMAP_MASTER.md, ROADMAP_INDEX.md)

**All artifacts must exist on disk and be valid (not placeholders or fixtures).**

## Validation Requirements

For completion, all of these must pass:

1. **Syntax validation**: `make quick` passes
2. **Full repo validation**: `make check` passes  
3. **Schema validation**: All YAML and JSON files are valid
4. **Integration validation**: Item is linked to dependent items and integration is proven
5. **Real-path validation**: Work is tested on real, not fixture-only, paths
6. **Rollback verification**: Rollback rule is defined and can be executed

## Rollback Semantics

Every item declares a `rollback_rule` in its YAML file that specifies:

- Which files can be safely deleted
- Which modifications can be reverted
- How to restore prior state if work must be undone

Rollback must be safe and leave no orphaned artifacts.

## Telemetry Requirements

Item completion must be recorded with:

- Completion timestamp
- Who completed it (session_id or human)
- Validation results summary
- Artifacts produced (list with file paths)

## Escalation Rules

If any validation fails, escalate:

- **Syntax failure**: Fix immediately, re-validate
- **Schema failure**: Fix immediately, re-validate
- **Integration failure**: Identify missing linkage, add, re-validate
- **Real-path failure**: Investigate root cause, fix, re-test
- **Rollback failure**: Fix rollback rule, re-validate

Do not claim completion if any escalation is outstanding.

## No Partial Work

Work is either complete or incomplete. There is no "mostly done" state.

An item is **incomplete** if any of these are true:

- Any expected artifact is missing or invalid
- Any validation fails
- Rollback rule is undefined or untested
- Integration is claimed but not proven with artifacts
- Roadmap surfaces are inconsistent

An item is **complete** only if all above criteria are met AND validated.

## Phase 0 Closure Specific

For Phase 0 closure, completion means:

1. All 6 items have valid YAML files
2. All supporting schemas exist and are valid
3. All 7 ADRs exist and are meaningful
4. CMDB-lite authority registry is current
5. Autonomy scorecard is updated
6. Definition of Done is documented (this file)
7. Validation script passes
8. Roadmap surfaces are consistent and show all items with status → completed
9. No duplicate or conflicting item references exist

The validation script (`bin/validate_phase0_closure.py`) must run to completion and report 100% success.

## Artifact File Checklist

Before claiming done, verify these files exist:

```
docs/roadmap/items/
  ✓ RM-AUTO-001.yaml
  ✓ RM-GOV-001.yaml (updated)
  ✓ RM-OPS-005.yaml
  ✓ RM-OPS-004.yaml
  ✓ RM-INV-002.yaml
  ✓ RM-DEV-001.yaml

governance/
  ✓ cmdb_lite.v1.yaml
  ✓ goal_intake_schema.v1.yaml
  ✓ execution_governance_schema.v1.yaml
  ✓ telemetry_event_schema.v1.yaml
  ✓ backup_restore_schema.v1.yaml
  ✓ asset_inventory_schema.v1.yaml
  ✓ apple_xcode_workflow.v1.yaml
  ✓ autonomy_scorecard.v1.yaml
  ✓ definition_of_done.v1.yaml
  
governance/adr/
  ✓ ADR-SESSION-SCHEMA.md
  ✓ ADR-TOOL-SYSTEM.md
  ✓ ADR-WORKSPACE-CONTRACT.md
  ✓ ADR-INFERENCE-GATEWAY.md
  ✓ ADR-PERMISSION-MODEL.md
  ✓ ADR-ARTIFACT-BUNDLE.md
  ✓ ADR-AUTONOMY-SCORECARD.md

schemas/
  ✓ execution_control_package.v1.json
  ✓ session_job_schema.v1.json
  
schemas/examples/
  ✓ execution_control_package_example.json

docs/standards/
  ✓ DEFINITION_OF_DONE.md (this file)

bin/
  ✓ validate_phase0_closure.py

artifacts/validation/
  ✓ phase0_closure_validation.json

docs/roadmap/
  ✓ ROADMAP_STATUS_SYNC.md (updated)
  ✓ ROADMAP_MASTER.md (updated)
  ✓ ROADMAP_INDEX.md (updated)
```

All must exist and be valid before work is considered complete.
