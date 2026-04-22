# RM-DEV-008 — Execution Pack

## Title

**RM-DEV-008 — Memory governance, summarization, and provenance policy for the local agent**

## Objective

Define how the local agent stores, summarizes, retrieves, and governs memory so that it becomes more useful without becoming noisy, unsafe, or weakly traceable.

## Why this matters

Memory can raise local-agent usefulness dramatically, but poorly governed memory becomes a source of drift, repetition, privacy leakage, and bad retrieval.

## Required outcome

- memory classes and retention rules
- summarization and compression policy
- provenance and confidence requirements
- retrieval eligibility rules
- feedback loop into coding/QC/autonomy workflows

## Required artifacts

- memory policy document
- memory schema/class model
- provenance/confidence fields
- retention/expiry rules
- retrieval governance matrix

## Best practices

- separate raw traces, summaries, durable patterns, and decision memory
- preserve provenance and confidence on memory items
- let retrieval depend on task class and trust level
- ensure memory helps bounded coding and QC instead of bloating prompts indiscriminately

## Common failure modes

- storing everything as equal-priority memory
- summaries with no source linkage
- retrieval with no confidence or relevance gating
- memory that cannot be cleaned, expired, or audited

## Recommended first milestone

Define the memory class model and provenance rules first, then build the retrieval governance matrix for coding, QC, and OSS-harvest workflows.
