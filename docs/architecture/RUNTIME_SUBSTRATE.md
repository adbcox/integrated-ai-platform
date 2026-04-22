# Shared Runtime Substrate

## Purpose

This document explains the shared runtime substrate that the platform must implement and why it sits beneath both the control plane and future domain branches.

## Why this matters

The central architectural gap is not general orchestration. It is the lack of a first-class runtime substrate with stable contracts.

Without the substrate, the platform risks:

- branch-specific execution loops
- inconsistent artifact handling
- unclear permissions and tool semantics
- shell-profile coupling
- local autonomy claims without comparable evidence

## Runtime substrate responsibilities

The shared runtime substrate is responsible for:

- canonical session/job schema
- typed tool model
- workspace controller
- permission enforcement
- sandbox execution
- command/execution interfaces
- artifact bundle and persistence behavior
- stable retry and run-state handling

## Canonical expectations

### Session/job schema

The substrate must expose a canonical session/job contract rather than allowing each branch or tactical package to invent its own execution metadata.

### Typed tools

Tools should be represented as typed callable surfaces with clear boundaries, expected inputs, and execution semantics.

### Workspace controller

The runtime should own:

- workspace creation
- workspace boundaries
- file access posture
- cleanup policy
- per-run isolation expectations

### Permission model

The runtime should decide what classes of actions are allowed, gated, or denied rather than leaving permission logic implicit in prompts or tactical wrappers.

### Sandboxing

Execution should occur within controlled sandbox rules, starting from lower-friction isolation and strengthening later as justified.

### Artifact contract

The runtime should emit a predictable artifact set so validation, promotion, and learning/reporting systems can compare runs consistently.

## Control-plane relationship

The control plane remains above the runtime substrate.

The control plane should:

- orchestrate
- qualify
- sequence
- budget
- promote
- supervise

The runtime substrate should:

- execute work through stable contracts
- manage tools/workspaces/permissions/artifacts
- make runs comparable and governable

## Domain-branch relationship

All branches must consume the same runtime substrate.

Branches may supply:

- branch-specific tools
- branch-specific workflows
- branch-specific prompts/adapters
- branch-specific UI and reporting

Branches may not replace:

- session/job contract
- workspace rules
- permission model
- artifact schema
- release evidence logic

## Immediate implementation priority

The runtime substrate must be prioritized before broad domain expansion because it is the main architectural dependency for:

- developer assistant proof
- local autonomy credibility
- repeatable validation
- anti-drift branch growth

## Reader shorthand

If a proposed feature or package requires a new execution backbone, it is probably violating the shared runtime substrate rule.
