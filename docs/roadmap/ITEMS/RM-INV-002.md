# RM-INV-002

- **ID:** `RM-INV-002`
- **Title:** Photo-driven inventory capture and capability mapping system for assets, components, consumables, and tools
- **Category:** `INV`
- **Type:** `System`
- **Status:** `Completed`
- **Maturity:** `M2`
- **Priority:** `High`
- **Priority class:** `P1`
- **Queue rank:** `8`
- **Target horizon:** `soon`
- **LOE:** `XL`
- **Strategic value:** `5`
- **Architecture fit:** `5`
- **Execution risk:** `3`
- **Dependency burden:** `3`
- **Readiness:** `near`

## Description

Build a photo-driven inventory capture and capability-mapping system that uses images plus user-provided information to identify, tag, and maintain records for complete devices, components, consumables, and tools, while giving the platform a materially better picture of owned capabilities, gaps, and reuse opportunities.

## Why it matters

This item turns physical assets into actionable system intelligence. It improves planning, capability awareness, purchase/gap analysis, reuse decisions, and future AI recommendations across multiple branches. It is one of the strongest bridges between the digital platform and the real-world environment it is supposed to support.

## Key requirements

- capture photo-backed records for assets, components, consumables, and tools
- support AI-assisted identification, tagging, and metadata enrichment
- retain persistent photos and normalized inventory records
- support capability-gap analysis and reuse/sell/retain reasoning over time
- explicitly support a Bambu filament library, computer component tracking, and full tool inventory
- remain compatible with future CMDB and broader asset/capability mapping surfaces

## Affected systems

- inventory and capability-mapping branch
- roadmap/CMDB linkage surfaces
- future procurement and gap-analysis views
- future control-center and dashboard views
- future agent planning that depends on real-world assets and capabilities

## Expected file families

- future inventory schema and record files
- future image intake/classification surfaces
- future capability-mapping logic
- future dashboard/reporting surfaces
- future asset/crosswalk documentation

## Dependencies

- governance and CMDB-linkage discipline
- consistent naming and asset identity rules
- future external-system and inventory integration posture where relevant

## Risks and issues

### Key risks

- could become an unstructured photo bucket if metadata discipline is weak
- duplicate records or low-confidence identification could reduce trust in the system
- mixing asset, component, consumable, and tool models too loosely could make the system messy over time

### Known issues / blockers

- the exact first bounded slice still needs careful shaping to avoid overreaching into full enterprise asset management on day one
- data hygiene and deduplication expectations must be designed early

## CMDB / asset linkage

- this item is explicitly adjacent to CMDB-lite and future asset/capability authority surfaces
- inventory records should remain linkable to systems, services, hosts, tools, and capability groups where relevant

## Grouping candidates

- `RM-GOV-001`

## Grouped execution notes

- Shared-touch rationale: this item shares asset identity, capability awareness, naming discipline, and CMDB-adjacent surfaces with governance and adjacent inventory work.
- Repeated-touch reduction estimate: high if normalized with other inventory/governance asset-model work instead of treated as a disconnected app idea.
- Grouping recommendation: `Bundle now`

## Recommended first milestone

Define a bounded inventory record model for assets, components, consumables, and tools; create a first intake flow using photos plus structured metadata; and prove that the system can support a small but real capability view covering Bambu filament, computer components, and tool inventory.

## Status transition notes

- Expected next status: `Decomposing`
- Transition condition: first bounded scope, record model, and intake path are explicitly defined
- Validation / closeout condition: a working initial capture-and-query slice exists and produces useful capability-aware inventory outputs

## Notes

This item should be treated as a foundational intelligence layer, not merely a storage convenience.