# Company Knowledge Base Operating Model

## Purpose

This document defines the operating model for the **company source-of-truth knowledge base** branch.

This branch exists to ingest company documents into a governed local knowledge system that can:
- preserve provenance,
- identify source authority,
- detect contradictions,
- support truth-resolution workflows,
- and provide a searchable internal memory layer for the wider AI system.

This is not just a generic RAG branch.
It is the company-document truth layer.

## Branch mission

Build a local-first, governed company knowledge base that turns company documents into one searchable, auditable, source-ranked truth layer.

## What this branch owns

This branch owns:
- company-document ingestion
- parsing and normalization of PDFs, Office files, HTML, images, scans, notes, and exports
- metadata extraction such as author, date, source class, version, and authority rank
- chunking, indexing, retrieval, and citation behavior
- contradiction detection and truth-resolution rules
- human review or override workflows for disputed facts
- evaluation of retrieval quality and faithfulness
- product and tool selection for local knowledge workbenching

## What this branch does not own

This branch does not own:
- Excel-to-web-app conversion
- website generation
- media acquisition
- media enhancement
- general-purpose dashboard work
- broad agent orchestration unrelated to company-document truth

## Operating assumptions from current system

This branch must align with the current repo operating model.

### Local-first posture
- local model runtime is primarily **Ollama**
- general local chat UI is primarily **Open WebUI**
- practical workspace-oriented local RAG is primarily **AnythingLLM**
- the branch should prefer existing local-stack role owners before introducing overlapping tools

### Governance posture
- canonical truth remains in repo-visible roadmap and governance surfaces
- summary docs do not override canonical item truth
- adoption decisions should remain explicit and role-based
- assistants should prefer reuse-first install, wrap, and thin integration patterns

### Working-method posture
This branch should be optimized for your current way of working:
- local-first execution where possible
- artifact-driven decisions instead of repeated re-derivation
- explicit runbooks and wrapper boundaries so coding assistants use less token budget
- heavy use of mature OSS and prebuilt modules instead of greenfield reimplementation

## Hardware posture

This branch must respect the hardware and startup policies already recorded elsewhere in the repo.

### When hardware matters
Document-ingestion and knowledge systems should:
- prefer local parsers and retrieval paths that fit the currently documented Mac and workstation hardware
- avoid heavy always-on services without explicit host-placement decisions
- prefer Dockerized or isolated deployment when dependency stacks are heavy
- keep parser, vector store, and workbench placement explicit when they become long-running services

### Deployment bias
- parser and ingestion toolchains should default to isolated environments
- always-on product-level workbenches should be justified against current host capacity
- cloud-first or OpenAI-dependent defaults are not acceptable as the starting architecture for this branch

## Truth model

The system must not treat “best retrieval score” as truth.

Truth should be ranked by explicit authority classes.

### Recommended authority hierarchy
1. final signed policy or official issued document
2. approved technical standard or controlled manual
3. site-specific as-built or implementation record
4. formal meeting record
5. working draft
6. informal note, email, or community commentary

### Additional resolution factors
When two sources conflict and their document class is the same, use:
- recency
- specificity
- source author role
- explicit approval state
- human-reviewed override if needed

## Preferred stack direction

### Parsing layer
Primary candidates:
- **Docling**
- **Unstructured** as comparison or fallback

### Retrieval and indexing layer
Primary candidates:
- **LlamaIndex**
- **ChromaDB**

Scale-up candidates:
- **Qdrant**
- **Haystack**

### Evaluation and truth-quality layer
Primary candidates:
- **RAGAS**
- **DeepEval**
- **Instructor**
- **OpenRefine** for metadata cleanup and normalization

### Product-level knowledge workbench candidates
Primary candidates to evaluate against the current stack:
- **RAGFlow**
- **Onyx**
- **Dify**
- **PrivateGPT**

Already aligned with current stack:
- **AnythingLLM**
- **Open WebUI Knowledge**

### Deferred complexity
Do not default to:
- GraphRAG
- Neo4j
- Celery and Redis worker platform
- custom broad ingestion UI
- custom OCR stack

These can be added later if the first bounded wave proves the need.

## Reuse-first rule

Before building custom code, assistants should check:
- `docs/architecture/KNOWLEDGE_INGESTION_REUSE_REGISTER.md`
- `docs/roadmap/KNOWLEDGE_INGESTION_IMPLEMENTATION_WAVE.md`

Assistants should prefer:
1. install the mature product if it cleanly owns the role
2. wrap and integrate the product if governance must remain local
3. reuse targeted modules or templates when only part of a stack is needed
4. defer when the tool is promising but not yet justified

## First-wave design intent

The first bounded implementation wave should establish:
- one parser path
- one indexing path
- one evaluation path
- one product-level knowledge workbench candidate beyond the current default stack
- one documented authority-ranking model for company documents

## Success criteria for this branch

This branch is materially successful when the repo truthfully contains:
- a canonical roadmap owner
- a reuse-first implementation wave
- a clear operating model
- role ownership for parsers, retrieval, evaluation, and workbench surfaces
- authority-ranking logic for company documents
- enough repo-visible structure that future assistants do not need to re-derive how to build the company knowledge base from scratch

## Notes

This branch should be treated as the company-document truth layer for the broader AI system.
Other branches may consume it later, but they should not redefine it.