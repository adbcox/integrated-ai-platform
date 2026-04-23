# Company Knowledge Base Toolchain Runbook

## Purpose

This runbook gives the practical install and usage posture for the first bounded company knowledge base branch.

Use it with:
- `docs/architecture/COMPANY_KNOWLEDGE_BASE_OPERATING_MODEL.md`
- `docs/architecture/KNOWLEDGE_INGESTION_REUSE_REGISTER.md`
- `docs/roadmap/KNOWLEDGE_INGESTION_IMPLEMENTATION_WAVE.md`
- `docs/roadmap/ITEMS/RM-KB-001.md`

## Branch intent

This branch exists to ingest company documents into a governed, source-ranked local knowledge base.

## Baseline stack for the first bounded wave

### Primary parser path
- Docling

### Comparison parser path
- Unstructured

### Retrieval and indexing
- LlamaIndex
- ChromaDB

### Evaluation and truth quality
- RAGAS
- DeepEval

### Already-preferred local knowledge surfaces
- AnythingLLM
- Open WebUI Knowledge
- Ollama

## Local-first deployment posture

- prefer isolated Python environments or Docker where dependency stacks are heavy
- keep parser and vector-store placement explicit when they become long-running services
- do not assume OpenAI or cloud APIs as default architecture
- align with current local model runtime posture already recorded elsewhere in repo docs

## Suggested environment layout

### Option A — isolated Python environment
Use for:
- parser and retrieval experiments
- local command-line ingestion
- early branch validation

Suggested package groups:
- docling
- unstructured
- llama-index
- chromadb
- ragas
- deepeval

### Option B — mixed local stack
Use when:
- AnythingLLM or Open WebUI Knowledge remains the daily-use surface
- ingestion and evaluation logic is developed in a separate local environment
- Ollama remains the local model runtime

## Suggested first install sequence

### 1. Parser path
Install and validate Docling first.

Then compare Unstructured against a representative subset of real company files.

### 2. Retrieval path
Install and validate:
- LlamaIndex
- ChromaDB

### 3. Evaluation path
Install and validate:
- RAGAS
- DeepEval

### 4. Platform-level candidate lane
Choose one primary candidate to evaluate first from:
- RAGFlow
- Onyx
- Dify
- PrivateGPT

Do not evaluate all as co-primary owners at once unless specifically justified.

## Example install posture

### Core branch packages
Example package set for the first bounded wave:

- `docling`
- `unstructured`
- `llama-index`
- `chromadb`
- `ragas`
- `deepeval`

### Typical local command pattern
Keep commands explicit in implementation packets. Examples include:
- parser smoke conversion
- vector-store persistence check
- retrieval query smoke test
- evaluation sample run

## Validation expectations

The branch should include validation samples for:
- complex PDF conversion
- Office-file conversion
- image or scan handling where relevant
- metadata extraction viability
- vector persistence
- retrieval quality
- contradiction or authority-ranking checks

## Authority model notes

Before broad ingestion starts, define metadata fields such as:
- source class
- author
- date
- version
- approval state
- authority rank

These should support source ranking and contradiction resolution later.

## Product-level candidate evaluation notes

### RAGFlow
Use when:
- company documents are layout-heavy, table-heavy, or chart-heavy
- harder documents are the real bottleneck

### Onyx
Use when:
- the branch needs a team-search or internal intelligence-layer style workbench

### Dify
Use when:
- workflow and app-building posture is central to how the branch will be used

### PrivateGPT
Use when:
- a Python-heavy local-first modular codebase is the main priority

## Current stack alignment notes

### AnythingLLM
Treat as:
- practical workspace-oriented knowledge surface
- useful operator-facing workbench
- not the only authority logic for source ranking

### Open WebUI Knowledge
Treat as:
- convenient general local knowledge interaction surface
- useful daily-use interface for uploaded libraries
- not the canonical source-of-truth logic by itself

### Ollama
Treat as:
- default local model runtime for this branch where model use is needed
- aligned with the current local-first stack

## What not to do in the first bounded wave

Do not default to:
- broad custom ingestion UI
- custom OCR stack
- GraphRAG
- Neo4j
- Celery and Redis worker architecture
- heavy always-on services without host-placement decisions
- cloud-first defaults

## Expected outputs from the first real execution pass

- parser comparison note
- selected primary parser
- retrieval and vector-store wrapper posture
- evaluation posture
- one selected platform-level candidate recommendation
- explicit company-document authority hierarchy
- exact validation and rollback notes

## Notes

This runbook is intentionally practical and bounded.
Use it to reduce token waste and repeated stack re-derivation when assistants start implementing the company knowledge base branch.