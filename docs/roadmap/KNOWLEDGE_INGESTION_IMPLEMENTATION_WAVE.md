# Knowledge Ingestion Implementation Wave

## Purpose

This document defines the first concrete reuse-first implementation wave for the company-document source-of-truth knowledge base.

It exists to convert research into a bounded execution packet so assistants install, wrap, or lightly modify mature OSS systems instead of recreating broad ingestion and RAG stacks from scratch.

## Scope of this wave

Included now:
- Docling
- Unstructured evaluation posture
- LlamaIndex
- ChromaDB
- RAGAS
- DeepEval
- one platform-level candidate evaluation from RAGFlow, Onyx, Dify, or PrivateGPT
- alignment with AnythingLLM and Open WebUI Knowledge already present in the preferred local stack
- company-document authority ranking and contradiction rules

Deferred from this wave:
- broad custom ingestion UI from scratch
- custom OCR pipeline from scratch
- full GraphRAG rollout
- generic Celery, Redis, and Neo4j platform rollout as the default first implementation path
- cloud-first or OpenAI-dependent default architecture

## Wave goals

1. define one practical parser path for complex local company documents
2. define one practical retrieval and indexing path for local knowledge storage
3. define one practical evaluation and truth-resolution path
4. define one product-level knowledge workbench candidate beyond the already preferred stack surfaces
5. make the authority model for company-document truth explicit and reusable
6. ensure this branch respects the current local hardware and operating model

## Wave inventory

### 1. Docling
- role: high-fidelity parsing and conversion primary candidate
- posture: adopt-selective and wrap
- required outputs: install path, wrapper boundary, supported file types for current needs, validation samples, rollback notes

### 2. Unstructured
- role: broad messy-document parser comparison candidate
- posture: adopt-selective and evaluate
- required outputs: fit comparison versus Docling, install posture, validation samples, adopt-or-defer criteria

### 3. LlamaIndex
- role: primary retrieval and indexing framework candidate
- posture: adopt-selective and wrap
- required outputs: install path, wrapper boundary, metadata and connector posture, validation samples

### 4. ChromaDB
- role: primary lightweight local vector store candidate
- posture: adopt-selective and wrap
- required outputs: storage posture, local placement notes, validation samples, rollback notes

### 5. RAGAS
- role: retrieval and truth-quality evaluation layer
- posture: adopt-selective and wrap
- required outputs: evaluation posture, example metrics to track, validation samples

### 6. DeepEval
- role: LLM and retrieval quality gate layer
- posture: adopt-selective and wrap
- required outputs: evaluation posture, example assertions or gates, validation samples

### 7. Platform-level candidate lane
Choose one primary platform candidate to evaluate first from:
- RAGFlow
- Onyx
- Dify
- PrivateGPT

Outputs required:
- primary candidate recommendation
- reasons to adopt or defer the others first
- install or evaluation posture
- validation path

### 8. Alignment with current stack
Document how this branch aligns with the already preferred current stack surfaces:
- AnythingLLM
- Open WebUI Knowledge
- Ollama

### 9. Company-document authority model
Required outputs:
- explicit authority hierarchy for company documents
- contradiction and truth-resolution rules
- metadata fields needed for authority scoring
- guidance on when human review is required

## Governing rules

- all adopted systems remain subordinate to canonical roadmap, validation, and local operating context
- prefer local-first and hardware-aware deployment
- do not introduce heavy always-on services without explicit host-placement decisions
- do not assume OpenAI or cloud dependencies as the default path
- do not broaden into GraphRAG, Celery, Redis, Neo4j, or full custom review UIs unless the first bounded wave proves they are needed

## Validation contract

The wave is only materially complete when:
- each selected system has a clear role and owner
- each selected system has install or wrap guidance
- each selected system has validation steps
- authority ranking and contradiction rules are explicit
- assistants no longer need to rethink whether to build these ingestion subsystems from scratch

## Relationship to roadmap

Primary owner:
- RM-KB-001

Secondary relevance:
- RM-GOV-009
- RM-INTEL-003
- RM-OPS-006

## Notes

This packet is the company-document truth-layer equivalent of the reuse-first implementation waves used for local AI coding and the media branches.