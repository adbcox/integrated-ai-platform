# Integrated AI Platform

Governed local-first AI operating system and control plane for autonomous business, personal, operational, and development workflows.

## What this repository is

This repository is the implementation and governance home for a platform whose broader mission is **not only AI coding**.

Its purpose is to provide:
- a central governed AI brain / control plane
- reusable connector and workflow infrastructure
- bounded local execution with evidence and validation
- multiple ingress channels for commands, ideas, and automation
- domain-specific autonomous functions built on one shared substrate

## Role of local coding autonomy

Local coding autonomy is a **foundational enabling capability** of the platform.
It is important because it lets the system improve, extend, and govern itself locally.

It is **not** the sole purpose of the platform.
The broader mission is autonomous and semi-autonomous execution across business, personal, operational, and development domains.

For the explicit mission/scope statement, read:
- `docs/architecture/SYSTEM_MISSION_AND_SCOPE.md`

For the full architecture source of truth, read:
- `docs/architecture/MASTER_SYSTEM_ARCHITECTURE.md`

For roadmap authority and current operating posture, read:
- `docs/roadmap/ROADMAP_AUTHORITY.md`
- `docs/governance/CURRENT_OPERATING_CONTEXT.md`
- `docs/roadmap/POST_CONVERGENCE_OPERATING_MODE.md`

## Current operating posture

The repository is operating in **post-convergence governed local-execution mode**.

That means:
- the local-autonomy substrate is treated as materially closed unless canonical repo truth shows regression
- future work should extend the governed platform instead of re-litigating the foundation by default
- bounded execution, artifact evidence, validation, and truth-surface sync remain mandatory
- roadmap closeout is not accepted until committed, pushed, and remote-visible

## Key operating layers

The platform is built around these layers:
- architecture and mission truth
- canonical roadmap item truth
- derived planning and dependency surfaces
- governed execution modes
- local-first implementation and validation substrate
- domain workflows and autonomous functions on top of the shared substrate

## Repo governance entry points

Start here when working in the repo:
- `docs/governance/CURRENT_OPERATING_CONTEXT.md`
- `docs/governance/DOCUMENT_STATE_INDEX.md`
- `docs/execution_modes/EXECUTION_ROUTER.md`
- `docs/governance/PROMPT_PACKET_STANDARD.md`

## Maintenance and validation

Run combined shell + Python syntax checks:

```sh
make check
```

Run fast changed-file checks:

```sh
make quick
```

Run deterministic offline behavior tests (no NAS/API dependency):

```sh
make test-offline
```

Run only offline scenarios affected by current file changes:

```sh
make test-changed-offline
```

## Local Aider tactical entry points

Fast local tactical Aider entry points:

```sh
make aider-fast
make aider-hard
make aider-smart
make aider-smart-status
```

Micro lane:

```sh
make aider-micro-help
make aider-micro-safe \
  AIDER_MICRO_MESSAGE="shell/common.sh::extract_session add guard for blank ids" \
  AIDER_MICRO_FILES="shell/common.sh"
```

## Tooling references

- `docs/execution_modes/LOCAL_AIDER_EXEC_MODE.md`
- `docs/execution_modes/CODEX_CONTROL_MODE.md`
- `docs/execution_modes/CODEX_EXEC_MODE.md`
- `docs/execution_modes/CLAUDE_CODE_EXEC_MODE.md`
- `docs/execution_modes/LOCAL_CONTROL_WINDOW_MODE.md`

## Notes

This repository contains implementation, governance, and operating surfaces for a broader AI operating platform.
Do not treat it as only a coding-assistant repo or only a browser-automation repo.
