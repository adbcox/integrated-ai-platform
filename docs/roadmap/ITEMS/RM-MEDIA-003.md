# RM-MEDIA-003

- **ID:** `RM-MEDIA-003`
- **Title:** Media inventory hygiene, duplicate detection, and cleanup advisory
- **Category:** `MEDIA`
- **Type:** `Enhancement`
- **Status:** `Completed`
- **Maturity:** `M1`
- **Priority:** `Medium`
- **Priority class:** `P3`
- **Queue rank:** `18`
- **Target horizon:** `later`
- **LOE:** `M`
- **Strategic value:** `3`
- **Architecture fit:** `5`
- **Execution risk:** `1`
- **Dependency burden:** `2`
- **Readiness:** `later`

## Description
Extend the media-control branch so the system can identify likely duplicate TV and movie files, flag conservative cleanup candidates, and generate approval-based cleanup recommendations.

## Why it matters
Improves media hygiene without requiring destructive automation by default.

## Key requirements
- duplicate detection
- conservative cleanup advisories
- approval-based cleanup posture

## Affected systems
- media inventory/control branch
- dashboard/reporting surfaces

## Expected file families
- future media-analysis logic and reports

## Dependencies
- `RM-MEDIA-001`
- `RM-MEDIA-002`

## Risks and issues
### Key risks
- false positives causing risky cleanup suggestions
### Known issues / blockers
- confidence thresholds and approval flow still need definition

## CMDB / asset linkage
- may later link to storage, library, and endpoint/media-service inventories

## Grouping candidates
- `RM-MEDIA-001`
- `RM-MEDIA-002`

## Grouped execution notes
- Shared-touch rationale: library inventory and media orchestration surfaces overlap.
- Repeated-touch reduction estimate: medium.
- Grouping recommendation: `Bundle after substrate exists`

## Recommended first milestone
Create a bounded duplicate-detection and review report for one media class with no destructive automation.

## Status transition notes
- Expected next status: `Decomposing`
- Transition condition: one media class, confidence posture, and review flow are defined
- Validation / closeout condition: one conservative cleanup-advisory slice exists with explicit operator approval
