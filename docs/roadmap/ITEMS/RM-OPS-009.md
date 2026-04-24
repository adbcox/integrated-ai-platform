# RM-OPS-009

- **ID:** `RM-OPS-009`
- **Title:** Caller identity, reverse phone lookup, and communication screening layer
- **Category:** `OPS`
- **Type:** `System`
- **Status:** `Accepted`
- **Maturity:** `M2`
- **Priority:** `Medium`
- **Priority class:** `P3`
- **Queue rank:** `18`
- **Target horizon:** `later`
- **LOE:** `M`
- **Strategic value:** `3`
- **Architecture fit:** `4`
- **Execution risk:** `3`
- **Dependency burden:** `3`
- **Readiness:** `later`

## Description

Build a governed caller-identity and communication-screening capability so the system can help identify unknown callers, reduce spam/noise, and provide structured context on inbound phone numbers without relying on low-quality ad-driven lookup sites.

The goal is not uncontrolled personal-data harvesting. The goal is a privacy-aware, source-aware workflow that uses reputable sources, explicit confidence levels, and lawful-use boundaries to help answer practical questions such as:

- who is calling me
- is this likely spam or legitimate
- have I seen this number before
- what source confidence do I have for the identity claim

## Why it matters

Phone calls and messages are a real operational input surface. The system should be able to help triage communication and identify likely spam or unknown callers in a way that is more useful and less exploitative than many consumer-facing reverse-lookup websites.

This also fits the broader platform direction of:
- centralizing inputs into the system
- improving operator decision support
- using governed connectors instead of ad hoc web searching

## Key requirements

- support reverse phone lookup through bounded, reputable, and reviewable source strategies
- show source confidence and provenance where possible
- support spam / likely-legitimate / unknown classification
- preserve a call/message history or local memory surface where useful
- support operator review rather than silent high-confidence assertions when evidence is weak
- support future integration into text/message ingress or assistant channels

### Privacy and lawful-use boundaries
- do not treat this as an unrestricted people-search or surveillance feature
- require explicit lawful-use posture and source-quality rules
- keep confidence/provenance visible rather than implying false certainty
- prefer public/business/contact and spam-identification context over invasive personal-detail enrichment
- preserve opt-in handling for any sensitive downstream use

## Affected systems

- communication ingress surfaces
- future text/message assistant channels
- connector/control-plane layer
- local operator dashboard and notification surfaces

## Expected file families

- future caller-intelligence connector docs/configs
- future source registry and confidence-policy files
- future message/call history surfaces
- future screening UI/state outputs

## Dependencies

- `RM-GOV-009` — external application connectivity and integration control plane
- `RM-UI-005` — local execution control and routing visibility surfaces
- future message/voice ingress items where communication channels are unified

## Risks and issues

### Key risks
- weak source quality leading to false identification
- privacy overreach if the feature drifts into unrestricted person enrichment
- overconfidence in identity claims where only partial evidence exists

### Known issues / blockers
- exact source strategy and confidence policy need explicit definition
- messaging/call ingestion posture should be aligned with the broader connector and ingress architecture

## CMDB / asset linkage

- low direct CMDB linkage; primarily an operator communication-intelligence surface

## Grouping candidates

- `RM-GOV-009`
- future message/voice ingress roadmap items
- future personal-assistant communication items

## Grouped execution notes

- Shared-touch rationale: communication ingress, connector governance, and operator notification surfaces overlap strongly.
- Repeated-touch reduction estimate: medium.
- Grouping recommendation: `Bundle after connector and command-ingress substrate is stable`

## Recommended first milestone

Define one bounded caller-screening slice using a small set of approved lookup or spam-identification sources, explicit confidence rules, and an operator-facing result format that does not overstate identity certainty.

## Status transition notes

- Expected next status: `Planned`
- Transition condition: source policy, confidence model, and one bounded intake path are defined
- Validation / closeout condition: one lawful, source-aware caller-screening slice works end to end with visible confidence and provenance

## Notes

This item should remain a communication-intelligence feature, not a general-purpose people-search system.