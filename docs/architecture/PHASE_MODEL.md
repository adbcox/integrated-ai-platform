# Architecture Phase Model

## Purpose

This document isolates the authoritative architecture phase model from the master architecture so phase reading stays stable and easy to reference.

## Phase 0 — Governance freeze and source-of-truth cleanup

Primary objective:
- lock ADRs
- lock execution-control package
- lock autonomy scorecard
- define version truth
- define architecture/runtime authority surfaces

## Phase 1 — Local runtime hardening for Ollama-first execution

Primary objective:
- stabilize local route
- introduce inference gateway
- standardize workspace layout and artifact persistence
- eliminate implicit shell/profile dependencies in application logic

## Phase 2 — Shared agent runtime substrate

Primary objective:
- canonical session/job schema
- typed tools
- workspace controller
- permission engine
- sandbox execution
- artifact bundle and conformance tests

## Phase 3 — Developer assistant MVP

Primary objective:
- prove the shared substrate through repo intake, repo understanding, patch/test/retry flow, result packaging, and repeatable benchmark behavior

## Phase 4 — Ollama self-sufficiency uplift

Primary objective:
- task-class prompt packs
- failure memory
- success prediction
- repo-pattern memory
- critique injection
- routing improvements

## Phase 5 — Qualification, regression, and local-autonomy gate closure

Primary objective:
- close promotion-governance gaps
- raise code-outcome coverage
- emit unified validation artifact
- formalize exception handling
- begin CMDB pilot only after coding stability is real

## Phase 6 — Controlled expansion after local coding independence

Primary objective:
- add controlled adapters
- broaden into non-coding branches
- preserve Ollama-first local route and shared runtime contract

## Reader shorthand

Use this phase model when deciding whether a roadmap item accelerates the actual architecture or merely expands surface area.
