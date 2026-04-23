# OSS Reuse and Adoption Register

## Purpose

This document defines the platform’s **reuse-first open-source adoption policy**.

It exists to stop coding assistants from re-creating capabilities that already exist in mature external repositories when those capabilities can be:
- installed as a full product,
- wrapped behind a repo-owned adapter,
- or reused as a focused library/module with only light modification.

## Core rule

Prefer the highest-leverage reuse path that preserves platform governance:

1. **Adopt as full product** when the external system already cleanly owns the whole role.
2. **Wrap and integrate** when the external system is strong but must sit behind repo-owned governance, policy, or routing.
3. **Reuse as library/module** when only part of the external repo is needed and simple modification or a thin adapter is sufficient.
4. **Defer** when the repo is promising but not yet justified.
5. **Reject-current-core** when the repo overlaps with a role already owned by a clearer primary choice.

## Reuse classes

### Adopt as full product
Use when the repo is already a coherent service/UI/workflow platform that the system should consume rather than rebuild.

### Wrap and integrate
Use when the repo is valuable but must remain subordinate to the governed platform.

### Reuse as library/module
Use when a focused component, SDK, CLI, or protocol surface can be pulled into the platform with light adaptation.

### Defer
Use when the repo is promising but not yet necessary.

### Reject-current-core
Use when the role is already covered by a clearer primary choice and adding the repo would increase drift.

## Register

| Repo / system | Preferred role | Reuse class | What to reuse | What not to rebuild | Notes |
|---|---|---|---|---|---|
| Ollama | Primary local model runtime | Adopt as full product | local runtime, model serving, API surface | do not rebuild a generic local model runner first | Primary runtime baseline |
| Open WebUI | General local chat UI | Adopt as full product | full self-hosted UI, multi-user/chat surface, model connectivity | do not build a generic chat UI before using this | Primary general local UI |
| AnythingLLM | Practical document/RAG workspace | Adopt as full product | document ingestion, workspace model, RAG/chat surface, supported connectors | do not rebuild a first-pass document chat workspace first | Primary practical RAG surface |
| Home Assistant Assist | Home / voice automation anchor | Adopt as full product | voice pipeline, home/device integration base | do not rebuild a general home voice stack first | Primary home voice anchor |
| Aider | Local coding executor | Wrap and integrate | CLI execution, repo-map/edit workflows, bounded code changes | do not rebuild a tactical coding editor/CLI loop first | Remains subordinate to governed execution |
| OpenHands | Dev-agent surface | Wrap and integrate | CLI/GUI dev-agent surface, bounded interactive execution | do not rebuild a parallel dev-agent UI before using bounded OpenHands surfaces | Subordinate, not authority |
| Dify | Workflow / AI app builder | Wrap and integrate | visual workflows, app builder, RAG/workflow layer | do not rebuild a generic low-code AI workflow studio first | Use as workflow layer only |
| LocalAI | Compatibility API bridge | Wrap and integrate selectively | OpenAI-compatible local API surface and broader multimodal local stack when needed | do not add by default if Ollama already covers the runtime role | Add only for justified compatibility breadth |
| LM Studio | Desktop/server local serving alternative | Adopt selectively / wrap | local serving UI, local server mode, host-specific deployments | do not build a host-specific GUI serving layer first | Host-fit alternative, not default backbone |
| RAGFlow | Advanced document understanding | Adopt selectively / wrap | deep document parsing, citation-heavy retrieval, heavier doc processing | do not build a bespoke complex-document RAG stack first | Use only when AnythingLLM-class surface is insufficient |
| RAG-Anything | Multimodal document RAG | Reuse as library/module or bounded subsystem | multimodal parsing/query pipeline, document processors, query methods | do not build multimodal doc parsing from scratch if this is the real need | Best fit for later multimodal document branch |
| MarkItDown | Document conversion utility | Reuse as library/module | Python library, CLI, optional MCP server pattern for document-to-markdown conversion | do not rebuild general Office/PDF/doc-to-markdown conversion | High-value ingest utility |
| PR-Agent | PR review automation | Wrap and integrate selectively | GitHub Action/self-hosted PR review workflow, local model integration posture | do not rebuild first-pass PR review automation from scratch | Best as bounded repo workflow addition |
| SonarQube Community Edition | Code quality and security gates | Adopt as full product or bounded quality service | code-quality scanning and gate service | do not build your own generic code quality platform first | Mature quality-gate candidate |
| Tabby | Self-hosted coding assistant | Defer / selective later | code completion server, editor integrations | do not add now while Aider already owns the primary coding-execution role | Useful later for completion/review branch |
| n8n | Visual workflow automation | Adopt selectively / wrap | visual workflows, node ecosystem, execution history | do not rebuild a generic visual workflow engine first | Strong later automation layer |
| Mem0 | Memory layer | Reuse as library/module selectively | OSS SDK/API for memory persistence and retrieval | do not build a generic memory SDK first if Mem0 fits the need | Only when memory becomes the bottleneck |
| vLLM | High-throughput inference server | Adopt selectively | throughput-oriented serving engine, OpenAI-compatible server | do not optimize for high-throughput server infrastructure before the use case exists | Heavy-serving candidate |
| llama.cpp | CPU / low-resource inference path | Reuse as library/module selectively | CPU/low-resource inference engine | do not build custom low-resource inference engine | Useful for constrained hosts only |
| OpenClaw | Messaging / assistant gateway | Defer, later evaluate for bounded reuse | channel integrations, skill model, sandboxed assistant gateway concepts | do not install as a casual second backbone | Promising, but large enough to require structured evaluation |
| GPT-Researcher | Research agent | Adopt selectively / wrap | research workflow and report generation pattern | do not build a full autonomous research pipeline from scratch before evaluating this | Candidate for research branch only |
| CrewAI | Multi-agent framework | Defer | orchestration patterns only if later justified | do not introduce now as a foundational layer | Not core now |
| AutoGen | Multi-agent framework | Defer | orchestration patterns only if later justified | do not introduce now as a foundational layer | Not core now |
| LLaMA-Factory | Fine-tuning / training | Defer | training/fine-tuning workflow only when track is formalized | do not start a fine-tuning stack before core operating stack is stable | Later only |
| Libra Chat | Overlapping local chat UI | Reject-current-core | none by default | do not add another primary local chat UI while Open WebUI owns the role | Rejected for current core |
| BrowserOS | Browser/agent surface | Reject-current-core | none by default | do not add another browser-agent backbone in parallel to computer-use branches | Rejected for current core |
| ADeus | Specialized wearable assistant | Reject-current-core | none by default | do not add specialized wearable assistant repo to current core stack | Rejected for current core |

## Assistant implementation rules

### 1. Reuse before rebuild
Before proposing a new implementation, assistants should check whether the role is already covered in this register.

### 2. Prefer bounded adapters
When reuse is allowed, prefer a thin repo-owned adapter or wrapper before forking or rewriting large external projects.

### 3. Fork only with explicit justification
Do not fork or vendor a large external repo unless:
- the role is core,
- the upstream tool is clearly missing a necessary capability,
- and a thin wrapper cannot solve the problem.

### 4. Preserve authority boundaries
Reused external systems must not become hidden planning or governance authorities.

### 5. Lean on mature code paths
If a mature external repo already provides:
- document ingestion,
- PR review,
- code-quality gates,
- workflow orchestration,
- or model serving,
assistants should prefer installing and integrating it rather than re-creating a weaker version.

## Relationship to roadmap items

This document is especially relevant to:
- `RM-GOV-009`
- `RM-UI-005`
- `RM-AUTO-001`
- `RM-HOME-005`
- `RM-INTEL-003`

## Notes

This register is designed to minimize drift and token use.
Future assistants should use it as a practical decision surface for whether to install, wrap, reuse, defer, or reject an open-source AI repository.