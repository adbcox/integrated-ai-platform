# RM-DEV-006 — Execution Pack

## Title

**RM-DEV-006 — Structure-aware code intelligence layer (Tree-sitter, LSP, structural search)**

## Objective

Add a structure-aware intelligence layer to the local development assistant using existing parsing, language-intelligence, and structural-search primitives rather than rebuilding them.

## Why this matters

This is one of the strongest direct intelligence improvements available for the local agent and a major follow-on from `RM-INTEL-002`.

## Required outcome

- parser/intelligence substrate selection
- structure-aware symbol and file intelligence model
- structural search/rewrite support
- integration path into repo maps, memory, and bounded coding workflows

## Required artifacts

- capability comparison matrix for Tree-sitter/LSP/structural search choices
- integration design note
- code intelligence schema or contract
- first structure-aware retrieval/search artifact or service spec

## Best practices

- use off-the-shelf parsing and protocol layers
- keep structure-aware intelligence separate from plain text search
- link symbol intelligence back to bounded codegen and QC flows
- preserve language-family extensibility

## Common failure modes

- reimplementing parsing or symbol extraction unnecessarily
- conflating indexed text search with structure-aware code understanding
- adding intelligence helpers without integrating them into actual coding workflows

## Recommended first milestone

Produce the capability comparison and integration contract first, then wire one structure-aware search/intelligence path into the local development assistant.
