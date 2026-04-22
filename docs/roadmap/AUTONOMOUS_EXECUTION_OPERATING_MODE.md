# Autonomous Execution Operating Mode

## Purpose

This document defines how the AI system should operate in loop-style mode when selecting, executing, validating, and then pulling the next roadmap task with minimal human interaction.

## Core rule

Autonomy is allowed only through the canonical architecture and roadmap governance system.

The AI may not improvise its own backlog, authority surfaces, or execution criteria.

## Loop model

The operating loop is:

1. read architecture truth
2. read roadmap status truth
3. read normalized active-item files
4. score eligible tasks using the target-selection policy
5. pull the best eligible task
6. execute within bounded scope
7. validate and update status/evidence surfaces
8. repeat

## Mandatory inputs before each loop

- `docs/architecture/MASTER_SYSTEM_ARCHITECTURE.md`
- `docs/roadmap/ROADMAP_STATUS_SYNC.md`
- `docs/roadmap/ROADMAP_MASTER.md`
- `docs/roadmap/ACTIVE_ITEM_NORMALIZATION_AUDIT.md`
- normalized per-item files for candidate tasks
- `docs/roadmap/TARGET_SELECTION_POLICY.md`

## Eligibility rule

The AI may only auto-pull items that are:

- normalized in per-item form
- architecture-aligned
- not blocked or unresolved by authority-surface ambiguity
- at sufficient maturity for bounded execution
- safe enough for low-oversight progression

## Stop / escalate conditions

The loop must stop or escalate when:

- a task lacks canonical definition
- multiple authority surfaces conflict
- a task requires unresolved external-system assumptions
- required documentation packs are missing
- the next step would expand scope rather than complete the bounded item
- validation evidence is insufficient to justify status progression

## Rule

Autonomy should increase throughput, not erode governance.
