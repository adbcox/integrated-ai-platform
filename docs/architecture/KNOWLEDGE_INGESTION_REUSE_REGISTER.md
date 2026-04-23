# Knowledge Ingestion Reuse Register

## Purpose

This document defines the reuse-first adoption posture for document ingestion, knowledge-base construction, truth resolution, and local knowledge workbench workflows.

This branch covers parsing, chunking, metadata extraction, retrieval frameworks, truth-resolution tooling, and user-facing knowledge systems.

## Core rule

For knowledge ingestion and document truth:
- prefer mature parsers for complex layouts instead of building custom PDF or OCR stacks
- prefer mature retrieval and orchestration frameworks over hand-built one-off RAG plumbing
- prefer complete local knowledge products when they already solve workspace, ingestion, and search well
- prefer thin wrappers, evaluation gates, and domain prompts over rebuilding full document platforms from scratch

## Knowledge reuse register

| System or repo | Role | Reuse mode | What to reuse | Notes |
|---|---|---|---|---|
| Docling | high-fidelity parsing and conversion | adopt-selective and wrap | PDF, Office, image, HTML conversion to structured markdown or JSON, OCR-capable local parsing | Strong primary parser candidate for complex layouts |
| Unstructured | broad messy-document parsing toolkit | adopt-selective and wrap | partitioning, connectors, chunk-ready preprocessing for many file types | Strong parser alternative or complement where file diversity is broad |
| LlamaIndex | retrieval and indexing framework | adopt-selective and wrap | connectors, retrieval orchestration, metadata-aware indexing, graph and router patterns | Strong primary retrieval framework candidate |
| LangChain and LangGraph | agentic document workflows | conditional and selective | stateful multi-step flows when retrieval must drive action logic | Use when graph or agent workflow need is proven |
| Haystack | enterprise-style pipeline framework | conditional and selective | structured auditable pipelines and evaluation-oriented retrieval flows | Good regulated or auditable branch candidate |
| Dify | unified AI app and RAG platform | adopt-selective and wrap | visual workflows, managed ingestion and agent orchestration | Strong UI-first platform candidate |
| RAGFlow | deep document understanding RAG platform | adopt-selective and wrap | hard-document extraction, citations, chunking and retrieval around complex documents | Strong candidate for difficult PDFs, tables, charts |
| Onyx | self-hosted team knowledge and search platform | adopt-selective and wrap | team search, agent and connector surface, internal search UX | Strong knowledge-workbench candidate |
| OpenContracts | contract and annotation truth platform | conditional and selective | annotation-driven source-of-truth workflows | Strong specialized truth-review candidate |
| Verba | local RAG application | conditional and selective | user-facing searchable RAG app patterns | Good product reference or selective deployment |
| AnythingLLM | local workspace-based knowledge system | adopt-now | workspace-oriented document ingestion and local RAG | Already aligned with current stack |
| Open WebUI Knowledge | local chat plus knowledge surface | adopt-now selective | knowledge libraries and upload-to-chat workflows | Good general daily-use knowledge surface |
| PrivateGPT | Python-heavy local RAG system | adopt-selective and reference | local-first ingestion and modular Python architecture | Strong codebase reference and selective deployment |
| Khoj | personal search and notes system | adopt-selective and reference | note-centric local search and background indexing patterns | Strong personal knowledge reference |
| LocalGPT | minimal local ingestion and chat system | reference-only selective | simple folder-ingest and local query patterns | Good lightweight reference |
| ChromaDB | local vector database | adopt-selective and wrap | lightweight persistent vector store for local branches | Strong local default candidate |
| Qdrant | vector database | adopt-selective and wrap | larger or more durable vector retrieval workloads | Good scale-up path |
| Neo4j | graph database | conditional and selective | graph relationships and GraphRAG where truly needed | Use only when relation-heavy workflows justify it |
| RAGAS | RAG evaluation | adopt-selective and wrap | faithfulness, context precision, retrieval evaluation | Strong evaluation layer candidate |
| DeepEval | LLM and retrieval evaluation | adopt-selective and wrap | unit-test style quality gates for LLM and RAG outputs | Strong evaluation layer candidate |
| OpenRefine | reconciliation and data cleaning | selective adopt and reference | metadata cleanup, entity normalization, deduplication | Strong pre-ingestion cleanup reference |
| Instructor | structured extraction layer | selective library reuse | schema-constrained metadata and fact extraction | Useful for strict metadata extraction |

## Preferred ownership by role

### A. Primary parsing layer
Primary current candidates:
- Docling
- Unstructured

### B. Retrieval and indexing layer
Primary current candidates:
- LlamaIndex
- ChromaDB

Scale or alternative candidates:
- Qdrant
- Haystack

### C. Unified knowledge platform layer
Primary current candidates:
- AnythingLLM
- Open WebUI Knowledge
- Dify
- Onyx
- RAGFlow

### D. Truth-resolution and evaluation layer
Primary current candidates:
- RAGAS
- DeepEval
- Instructor
- OpenRefine

### E. Graph and relationship layer
Conditional candidate:
- Neo4j

## Assistant rules

1. Do not build a custom parser before testing Docling or Unstructured against the actual document mix.
2. Do not build a broad custom knowledge UI before checking whether AnythingLLM, Open WebUI Knowledge, Onyx, Dify, or PrivateGPT already solve the role.
3. Use evaluation frameworks for truth and conflict checks instead of relying only on ad hoc prompts.
4. Only introduce Neo4j or GraphRAG when relation-heavy workflows justify the added complexity.
5. Keep all knowledge systems subordinate to local governance, hardware constraints, and canonical roadmap truth.

## Hardware and operating-model notes

This branch must respect the current local-first system setup:
- local model runtime is primarily Ollama
- general local chat UI is primarily Open WebUI
- practical workspace-oriented local RAG is primarily AnythingLLM
- the system should prefer the existing hardware posture and approved model startup policies recorded elsewhere in repo governance

When hardware matters:
- prefer local parser and retrieval paths that run well on the currently documented Mac and workstation hardware
- avoid introducing heavy always-on services without a clear host-placement decision
- prefer Dockerized or isolated deployment where dependency stacks are heavy

## Recommended first-wave knowledge reuse targets

1. Docling
2. LlamaIndex
3. ChromaDB
4. RAGAS
5. one platform-level candidate from RAGFlow, Onyx, Dify, or PrivateGPT
6. AnythingLLM and Open WebUI Knowledge alignment with current stack

## Relationship to roadmap

This document is especially relevant to:
- RM-KB-001
- RM-GOV-009
- RM-INTEL-003
- RM-OPS-006

## Notes

This register is intended to make the knowledge-ingestion branch reuse-first by default.