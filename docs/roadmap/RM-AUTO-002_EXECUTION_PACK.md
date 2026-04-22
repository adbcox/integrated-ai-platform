# RM-AUTO-002 — Execution Pack

## Title

**RM-AUTO-002 — Roadmap-to-execution compiler and batch prompt builder**

## Objective

Convert selected roadmap items and grouped packages into governed execution bundles, prompts, and validation plans that can be handed to implementation systems consistently.

## Why this matters

The roadmap becomes operational only when it can generate execution-ready artifacts reliably.

## Required outcome

- roadmap selection input model
- execution bundle schema
- prompt-builder rules
- validation/rollback sections in generated outputs
- grouped-package support

## Required artifacts

- roadmap-to-execution schema
- prompt template library
- compiled execution bundle artifact
- validation/rollback template

## Best practices

- preserve roadmap IDs and dependencies in compiled outputs
- include allowed files, forbidden files, validation order, and rollback rules by default
- support grouped parent/child execution packages
- keep the compiler deterministic and reviewable

## Common failure modes

- prompts generated with no dependency or validation context
- bundle generation that loses roadmap IDs or grouping relationships
- auto-generated prompts that are too vague to execute safely

## Recommended first milestone

Define the execution-bundle schema and generate the first roadmap-to-execution compilation for a bounded high-priority package.
