# RM-OPS-003

- **ID:** `RM-OPS-003`
- **Title:** Outdoor activity readiness display with air quality, humidity, temperature, and combined suitability score
- **Category:** `OPS`
- **Type:** `Feature`
- **Status:** `In progress`
- **Maturity:** `M1`
- **Priority:** `High`
- **Priority class:** `P3`
- **Queue rank:** `5`
- **Target horizon:** `later`
- **LOE:** `M`
- **Strategic value:** `4`
- **Architecture fit:** `3`
- **Execution risk:** `1`
- **Dependency burden:** `2`
- **Readiness:** `later`

## Description
Build a health-aware outdoor readiness display that combines air quality, humidity, and temperature into an activity suitability score.

## Why it matters
Transforms raw environmental data into a practical decision surface, especially valuable for asthma-sensitive use.

## Key requirements
- display AQ/humidity/temperature
- produce combined suitability rating
- highlight limiting factor
- keep UX simple and health-aware

## Affected systems
- ops/environment reporting surfaces
- control center and ambient dashboards

## Expected file families
- future display cards and scoring logic

## Dependencies
- environment/weather data sources
- related dashboard surfaces

## Risks and issues
### Key risks
- simplistic scoring that hides key health nuance
### Known issues / blockers
- final weighting model should remain explainable

## CMDB / asset linkage
- no major asset linkage beyond display surfaces and optional local sensor context

## Grouping candidates
- `RM-HOME-001`
- `RM-UI-003`
- `RM-UI-004`

## Grouped execution notes
- Shared-touch rationale: environment cards and tablet/dashboard surfaces overlap.
- Repeated-touch reduction estimate: medium.
- Grouping recommendation: `Bundle after substrate exists`

## Recommended first milestone
Create one outdoor-readiness card with explicit factor weighting and explanation text.

## Status transition notes
- Expected next status: `Decomposing`
- Transition condition: scoring model and display surface are bounded
- Validation / closeout condition: one working outdoor-readiness display exists with explainable outputs
