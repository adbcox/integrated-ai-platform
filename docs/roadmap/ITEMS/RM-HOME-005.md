# RM-HOME-005

- **ID:** `RM-HOME-005`
- **Title:** Local voice and ambient assistant layer for Alexa/Google Home replacement using Home Assistant as the device bridge
- **Category:** `HOME`
- **Type:** `System`
- **Status:** `In progress`
- **Maturity:** `M2`
- **Priority:** `High`
- **Priority class:** `P2`
- **Queue rank:** `2`
- **Target horizon:** `soon`
- **LOE:** `L`
- **Strategic value:** `5`
- **Architecture fit:** `5`
- **Execution risk:** `2`
- **Dependency burden:** `3`
- **Readiness:** `near`

## Description

Build a local voice and ambient assistant layer intended to replace Alexa / Google Home style device interaction in the environment, using Home Assistant as the device/entity bridge while keeping policy, reporting, higher-level orchestration, and user experience in this platform.

The core principle is:

- Home Assistant handles device/entity integration and low-level automation connectivity
- this platform owns the higher-level assistant logic, dashboard integration, room-role behavior, reporting, and future agentic control patterns

This item should support tablet/ambient displays, room-oriented control surfaces, and future voice hardware or Home Assistant voice endpoints without turning Home Assistant into the primary user-facing system.

## Why it matters

This is one of the most direct user-facing ways to make the platform replace mainstream assistant products while preserving local control. It also aligns closely with the existing home/dashboard direction and the desire to replace Alexa-like devices with tablet and ambient surfaces already in the roadmap.

It has high leverage because it:

- makes the platform immediately useful in daily life
- reinforces Home Assistant as the device bridge rather than requiring custom per-device integrations
- aligns with the local-first, privacy-preserving system direction
- gives the dashboard and ambient display work a clear operating purpose

## Key requirements

### Voice and ambient interaction
- local or local-preferred voice-command workflow
- room-aware assistant behavior
- ambient response surfaces for tablets/displays
- clear distinction between deterministic home control and broader conversational AI

### Explicit voice-stack adoption posture now in scope
- **Home Assistant Assist** is the preferred home/voice anchor
- use Home Assistant voice pipelines and entity/device bridge posture before building custom broad voice infrastructure
- **Whisper** may be adopted later as a branch-specific transcription substrate where a specific local transcription need justifies it
- do not add overlapping voice-assistant stacks as co-primaries without explicit bounded justification
- treat broader local AI chat UIs as secondary to the dedicated home/voice path for this item

### Home Assistant bridge posture
- use Home Assistant for entity/device bridging
- use Home Assistant for supported low-level automation and device control
- keep assistant UX, reporting, room behavior, and policy logic in this platform
- do not make Home Assistant the canonical roadmap or control authority

### Control and safety
- support deterministic command execution for home actions
- support explicit confirmation rules for higher-risk commands
- support mute/privacy posture where voice endpoints are involved
- expose status and action history in the local dashboard/control layer

### Dashboard and ambient display integration
- integrate with existing ambient/tablet roadmap items
- support room-specific voice/ambient widgets and status cards
- show current room/device state and recent assistant actions

## Affected systems

- home automation branch
- ambient dashboard / tablet UI branch
- Home Assistant integration boundary
- future voice endpoint / microphone / speaker surfaces
- control-center and reporting surfaces
- local voice stack adoption posture

## Expected file families

- future voice/ambient orchestration docs
- future Home Assistant adapter or capability-binding files
- future room/assistant policy files
- future dashboard widgets and room-role UI surfaces
- future local transcription integration notes if later justified

## Dependencies

- `RM-HOME-001` — indoor air quality monitoring and purifier automation app with Home Assistant integration
- `RM-UI-003` — tablet-specialized ambient control dashboards to replace Alexa-type devices
- `RM-UI-004` — ambient tablet display themes for kitchen, entertainment, and hallway use
- `RM-UI-005` — local execution control and routing system where local assistant execution patterns may later be routed/governed
- `RM-GOV-009` — external application connectivity and integration control plane
- external Home Assistant voice / device bridge posture where applicable

## Risks and issues

### Key risks
- over-expanding from deterministic smart-home control into a vague general assistant before the home-control base is solid
- weak privacy/mute posture for always-available voice endpoints
- creating overlapping UX between Home Assistant and this platform
- introducing multiple overlapping voice stacks without one clear primary anchor

### Known issues / blockers
- exact first voice endpoint and room-role implementation path still needs bounding
- should not outrun the underlying ambient display and Home Assistant bridge work
- voice-stack adoption posture should remain synchronized with the local AI stack role matrix and external integrations catalog

## CMDB / asset linkage

- should later link room devices, tablets, voice endpoints, and automation-capable hardware into the inventory/CMDB-adjacent model
- should expose room/device capability state relevant to assistant actions

## External dependency documentation pack

- **Official docs home:** Home Assistant and any chosen local voice endpoint / voice pipeline docs
- **Primary repo or vendor page:** Home Assistant and related adopted voice endpoint components
- **API / integration docs:** Home Assistant entity/device APIs and local voice interfaces where used
- **Auth / permission docs:** must preserve local auth/privacy posture
- **Installation / deployment docs:** local-first deployment only
- **Known caveats / integration constraints:** Home Assistant remains the device bridge; this platform remains the higher-order assistant/control surface
- **Adoption note:** `adopt-now`

## Grouping candidates

- `RM-HOME-001`
- `RM-UI-003`
- `RM-UI-004`
- `RM-GOV-009`

## Grouped execution notes

- Shared-touch rationale: home-automation bridge, ambient display UX, and external integration governance overlap strongly.
- Repeated-touch reduction estimate: high.
- Grouping recommendation: `Bundle after ambient/dashboard substrate is stable`

## Recommended first milestone

Define and implement one bounded room-level voice/ambient control slice using Home Assistant as the device bridge and this platform as the visible assistant/control surface.

That first slice should explicitly use the preferred home/voice stack posture rather than introducing overlapping voice systems.

## Status transition notes

- Expected next status: `Planned`
- Transition condition: first room, first supported voice/ambient command set, Home Assistant bridge boundary, and preferred voice-stack posture are explicitly defined
- Validation / closeout condition: one room-level voice/ambient assistant slice works end to end with visible status/history and clear privacy/control rules

## Notes

This item should be treated as the canonical roadmap home for Alexa/Google Home replacement behavior built on local-first principles rather than as a generic “voice assistant” idea.