# RM-KB-001

- **ID:** `RM-KB-001`
- **Title:** Company document ingestion and source-of-truth knowledge base
- **Category:** `KB`
- **Type:** `System`
- **Status:** `In progress`
- **Maturity:** `M2`
- **Priority:** `High`
- **Priority class:** `P2`
- **Queue rank:** `10`
- **Target horizon:** `next`
- **LOE:** `L`
- **Strategic value:** `5`
- **Architecture fit:** `5`
- **Execution risk:** `3`
- **Dependency burden:** `3`
- **Readiness:** `near`

## Description

Build a local-first, governed company knowledge base that ingests company documents and turns them into one searchable, source-ranked truth layer for the broader AI system.

This is not a generic RAG item.
It is the canonical branch for company-document truth.

## Why it matters

The platform needs one internal memory layer that can:
- ingest company documents,
- preserve provenance,
- rank source authority,
- detect contradictions,
- support truth resolution,
- and expose the resulting knowledge to later assistants and workflows.

Without this branch, company knowledge remains fragmented across folders, document styles, exports, and local memory, which weakens the usefulness of the wider AI system.

## Governing sources

This item is governed by:
- `docs/architecture/KNOWLEDGE_INGESTION_REUSE_REGISTER.md`
- `docs/architecture/COMPANY_KNOWLEDGE_BASE_OPERATING_MODEL.md`
- `docs/roadmap/KNOWLEDGE_INGESTION_IMPLEMENTATION_WAVE.md`
- `docs/roadmap/EXTERNAL_APPLICATIONS_AND_INTEGRATIONS.md`

## Key requirements

### Core branch goals
- ingest company documents from local and approved connected sources
- parse and normalize complex files into reusable internal representations
- extract metadata such as author, date, version, source class, and authority rank
- support chunking, indexing, retrieval, and citations
- detect contradictions across sources
- apply explicit truth-resolution rules
- support human review for disputed or ambiguous facts
- provide operator-facing knowledge workbench capabilities under local governance

### Explicit authority model now in scope
The branch must define and use a source hierarchy such as:
1. final signed policy or official issued document
2. approved technical standard or controlled manual
3. site-specific as-built or implementation record
4. formal meeting record
5. working draft
6. informal note, email, or commentary

When source class is equal, compare:
- recency
- specificity
- author role
- approval state
- human-reviewed override

### Preferred technical ownership now in scope
- **Docling** — primary parsing candidate
- **Unstructured** — comparison or fallback parsing candidate
- **LlamaIndex** — primary retrieval and indexing framework candidate
- **ChromaDB** — primary lightweight local vector store candidate
- **RAGAS** — retrieval and truth-quality evaluation candidate
- **DeepEval** — LLM and retrieval quality-gate candidate
- **AnythingLLM** — current practical workspace-oriented local knowledge surface
- **Open WebUI Knowledge** — current general local knowledge surface

### Platform-level candidate lane now in scope
Choose one primary evaluation candidate from:
- RAGFlow
- Onyx
- Dify
- PrivateGPT

Do not treat all of them as simultaneous co-primary owners of the same role.

## Affected systems
- company-document ingestion branch
- local knowledge workbench surfaces
- retrieval and citation surfaces
- contradiction and truth-resolution flows
- future assistant and dashboard consumers of company-document truth

## Expected file families
- `docs/architecture/*`
- `docs/roadmap/*`
- future parser and ingestion wrapper files
- future retrieval and evaluation wrapper files
- future config templates and runbooks
- future bounded knowledge workbench integration files

## Dependencies
- `RM-GOV-009`
- `RM-INTEL-003`
- `RM-OPS-006`
- current local AI stack runbook and hardware guidance

## Risks and issues

### Key risks
- building a generic RAG toy instead of a governed company truth layer
- overcomplicating the first wave with GraphRAG or heavy worker infrastructure too early
- introducing overlapping knowledge products without role clarity
- failing to make authority ranking explicit
- allowing chat or summary surfaces to override canonical knowledge-source logic

### Known issues and blockers
- exact document-source inventory and priority order still need to be formalized later
- one primary platform-level candidate should be chosen before broadening into overlapping products
- host placement and always-on service decisions should stay explicit and hardware-aware

## Recommended first milestone

Complete the first knowledge-ingestion reuse wave:
- Docling
- Unstructured comparison posture
- LlamaIndex
- ChromaDB
- RAGAS
- DeepEval
- one primary platform-level candidate
- explicit company-document authority hierarchy

## Status transition notes
- Expected next status: `Decomposing`
- Transition condition: selected parsers, retrieval layer, vector store, evaluation layer, platform-level candidate, and authority model are explicitly defined with install or wrap posture
- Validation and closeout condition: the repo has a truthful, bounded, reuse-first implementation package for the company knowledge base branch and assistants no longer need to re-derive whether to build the branch from scratch

## Notes

This item is the canonical roadmap home for company-document ingestion and source-of-truth knowledge-base construction.