# RM-INV-003

- **ID:** `RM-INV-003`
- **Title:** Live product search, pricing history, and inventory-aware procurement workflow
- **Category:** `INV`
- **Type:** `System`
- **Status:** `Completed`
- **Maturity:** `M2`
- **Priority:** `High`
- **Priority class:** `P3`
- **Queue rank:** `8`
- **Target horizon:** `later`
- **LOE:** `L`
- **Strategic value:** `4`
- **Architecture fit:** `4`
- **Execution risk:** `2`
- **Dependency burden:** `3`
- **Readiness:** `later`

## Description

Support real product discovery with live listings, in-stock verification, historical pricing context, watchlists, and future linkage to owned hardware and procurement needs.

This item now explicitly includes a hardware/resource-aware upgrade-evaluation model so the system can assess whether new purchases yield meaningful performance gain relative to current owned systems and workloads.

## Why it matters

Extends inventory and capability awareness into practical procurement intelligence.

It should not merely tell the user what products exist. It should help answer:

- what purchase is worth making next
- what performance gain is actually likely in this environment
- whether the gain is meaningful for real workloads
- whether the improvement is justified by cost, complexity, and integration burden

That makes this item a critical bridge between product search and real decision support.

## Key requirements

- live product discovery
- pricing history / context
- watchlists and procurement review
- linkage to owned inventory and compatibility context
- performance-aware upgrade evaluation for relevant hardware classes
- justified cost / performance / fit scoring rather than naive benchmark comparison

### Hardware ROI / upgrade-value model now in scope

This item should define and later implement a composite evaluation metric that combines:

- estimated performance gain for target workloads
- utilization weight for how often the subsystem matters
- compatibility / fit with owned systems
- bottleneck relief value
- total acquisition cost
- integration/migration overhead
- uncertainty / risk penalty

A recommended canonical starting metric is:

**Weighted Upgrade Value (WUV)**

`WUV = ((Estimated Performance Gain %) × Utilization Weight × Fit Score × Bottleneck Relief Score) / (Total Upgrade Cost + Integration Cost + Risk Penalty)`

This metric should be adapted per hardware class rather than treated as one universal fixed formula, but the roadmap item should explicitly require a justified cost-to-performance framework of this type.

## Affected systems

- inventory/capability branch
- procurement and recommendation surfaces
- future dashboards/control surfaces
- hardware resource manager and capability planning surfaces

## Expected file families

- future product search/adapters
- pricing/history and recommendation logic
- future upgrade-evaluation metric docs/configs
- future compatibility and workload-model files

## Dependencies

- `RM-INV-001`
- `RM-INV-002`
- future external product/price connector posture through governance surfaces

## Risks and issues

### Key risks
- poor distinction between owned inventory and market listings
- using generic benchmark logic that does not match real workloads
- overconfidence in performance estimates where workload signals are weak

### Known issues / blockers
- exact external data sources and trust rules need bounding
- workload-specific performance modeling needs explicit first-class boundaries

## CMDB / asset linkage

- should remain linkable to owned assets, capability gaps, and compatible target systems
- should link procurement recommendations to current hardware resource state and bottleneck information where available

## Grouping candidates

- `RM-INV-001`
- `RM-INV-002`
- `RM-GOV-009`

## Grouped execution notes

- Shared-touch rationale: inventory, capability, procurement, and external product/price integration surfaces overlap.
- Repeated-touch reduction estimate: high.
- Grouping recommendation: `Bundle now`

## Recommended first milestone

Define a bounded procurement workflow that links live product lookup to owned-inventory context for one hardware class.

The first slice should also define a justified upgrade-evaluation model for that same hardware class so the system can produce a real recommendation, not just a listing.

## Status transition notes

- Expected next status: `Decomposing`
- Transition condition: one product class, one external data strategy, and one workload-aware upgrade-evaluation model are explicitly defined
- Validation / closeout condition: a bounded procurement-intelligence slice exists and uses owned-inventory context and justified upgrade-value scoring meaningfully
