# Roadmap Item Template

## Header

- **ID:** `RM-XXX-000`
- **Title:**
- **Category:**
- **Type:** `Program | System | Feature | Enhancement`
- **Status:**
- **Priority:**
- **Priority class:**
- **Queue rank:**
- **Target horizon:**
- **LOE:**
- **Strategic value:**
- **Architecture fit:**
- **Execution risk:**
- **Dependency burden:**
- **Readiness:**

## Description

Describe the item in direct operational terms.

## Why it matters

Explain the practical value and system-level importance.

## Key requirements

- requirement 1
- requirement 2
- requirement 3

## Affected systems

- system / subsystem
- dashboard / UI surface
- integration layer

## Expected file families

- file family 1
- file family 2

## Dependencies

- dependency 1
- dependency 2

## CMDB / asset linkage

- asset or service 1
- asset or service 2

## External dependency documentation pack

Complete this section whenever the roadmap item depends on an external product, service, API, protocol, OSS application, or major third-party integration.

- **Official docs home:**
- **Primary repo or vendor page:**
- **API reference:**
- **Auth / OAuth / permission docs:**
- **Installation / deployment docs:**
- **Configuration docs:**
- **Webhook / event docs:**
- **Rate limits / quotas:**
- **Changelog / release notes:**
- **Version / compatibility notes:**
- **Known caveats / integration constraints:**
- **Adoption note:** `adopt-now | evaluate | watch | reject`

## Grouping candidates

- `RM-...`
- `RM-...`

## Grouped execution notes

- Shared-touch rationale:
- Repeated-touch reduction estimate:
- Grouping recommendation:

## Recommended first milestone

Define the smallest useful and coherent first implementation slice.

## Notes

Optional implementation, risk, or sequencing notes.

## Mandatory intake synchronization checklist

Before considering the roadmap intake complete:

- [ ] Add or update the normalized item entry in `docs/roadmap/ROADMAP_INDEX.md`
- [ ] Check whether this intake changes strategic priority, pull order, or roadmap ranking
- [ ] If yes, update `docs/roadmap/ROADMAP_MASTER.md` in the same intake cycle
- [ ] If detailed normalization is needed, add a dated sync/supporting file under `docs/roadmap/`
- [ ] Create or assign dedicated execution-pack coverage, or explicitly record canonical enrichment coverage and the path to later execution-pack treatment
- [ ] Add or update `docs/roadmap/EXECUTION_PACK_INDEX.md` if a dedicated execution pack exists
- [ ] If the item depends on an external integration, complete or link the verified documentation pack
- [ ] Do not leave the item only in chat, issues, or legacy `roadmap/` files
