# Reference Implementations and Public Templates

## Purpose

This document catalogs **forkable reference implementations** and **public templates** that the platform should evaluate before writing new code.

It exists to reduce:
- unnecessary greenfield implementation,
- token waste from re-deriving common subsystems,
- drift caused by inventing weaker first-pass versions of mature external systems.

This document complements:
- `docs/architecture/LOCAL_AI_STACK_ROLE_MATRIX.md`
- `docs/architecture/OSS_REUSE_AND_ADOPTION_REGISTER.md`
- `docs/roadmap/EXTERNAL_APPLICATIONS_AND_INTEGRATIONS.md`

## Core rule

When a repo already provides a functional implementation of a needed subsystem, assistants should prefer one of these paths:

1. **Fork or install the full system** when the whole product is the right role owner.
2. **Wrap the system** when the product is strong but must remain subordinate to repo-owned governance.
3. **Reuse targeted modules or templates** when only a subsystem is needed.
4. **Defer** when the repo is promising but not yet worth integrating.

Do **not** assume new code should be written first.

## Reference implementation register

| System / repo | Role | Reuse mode | Reuse target | Notes |
|---|---|---|---|---|
| `opencode-ai/opencode` | Terminal coding-agent reference | selective fork / module reuse | TUI patterns, MCP/tool integration posture, session/config structure | Strong direct terminal-agent reference; repo is archived/publicly frozen, so treat as design/code reference rather than future backbone. citeturn675469search3turn675469search2 |
| `OpenHands/OpenHands` | Dev-agent, sandboxed execution, GUI/CLI surface | wrap and integrate | full product selectively; execution UI and sandbox model | High-value reference and optional installed surface; keep subordinate to governed execution. citeturn675469search1 |
| `stitionai/devika` | plan/execute/verify coding-agent reference | selective reuse | planning loop, error parsing, multi-step coding flow patterns | Treat as a lighter reference implementation for repair/state-loop ideas. |
| `meltylabs/melty` | AI-first IDE / code-intent reference | defer / targeted later reuse | IDE/extension patterns, code-intent UX ideas | Useful for later IDE-native branch, not current core stack. |
| `plandex-ai/plandex` | context slicing, change-set and rollback model | targeted module reuse | context trimming concepts, change-set/rollback patterns | Strong fit for context-budget and rollback logic; do not rebuild from scratch if these are the real bottlenecks. |
| `gpt-engineer-org/gpt-engineer` | app-generation and improve-loop reference | targeted template reuse | prompt templates and improve-loop patterns | Use as prompt/template source, not backbone. |
| `Significant-Gravitas/AutoGPT` | long-running task/server reference | defer / selective later reuse | queueing and long-running agent concepts only if later justified | Not foundational now. |
| `modelcontextprotocol/servers` | official MCP reference servers | reuse as official reference modules | filesystem, fetch, git, memory, sequential-thinking, time reference servers | These are explicitly reference implementations, not guaranteed production-ready products. Use as canonical examples and thinly wrapped tools. citeturn245548search1 |
| `TabbyML/tabby` | self-hosted coding completion/review system | defer / selective later reuse | code completion/review branch reference | Strong later candidate, not current Aider replacement. |
| `qodo-ai/pr-agent` | PR review and PR automation | adopt-selective / wrap | GitHub Action, Docker, webhook, PR commands, prompt config | Good fit for PR review automation instead of writing first-pass PR reviewer logic. citeturn245548search3 |
| `SonarSource/sonarqube` | code-quality and security gate platform | adopt as full product or bounded service | full service for quality gates | Prefer mature quality gates over custom first-pass scanners. |
| `n8n-io/n8n` | visual workflow automation platform | adopt-selective / wrap | full workflow platform, node ecosystem, AI workflow nodes | Strong workflow layer candidate; self-hostable and large integration base. citeturn245548search5turn245548search0 |
| `microsoft/markitdown` | document conversion utility | reuse as library/module | CLI + library for doc-to-markdown conversion | Strong ingest utility; do not rebuild broad doc conversion. |
| `HKUDS/RAG-Anything` | multimodal RAG reference | targeted later reuse | multimodal document ingestion/querying | Use if multimodal docs become a hard requirement. |
| `infiniflow/ragflow` | advanced document understanding / citation-heavy RAG | adopt-selective / wrap | full product or bounded subsystem | Heavier document/RAG system; use when AnythingLLM-class posture is insufficient. |
| `assafelovic/gpt-researcher` | research/reporting agent | adopt-selective / wrap | research workflow and report generation | Candidate for research branch. |
| `continuedev/continue` | local model IDE integration reference | defer / selective later reuse | extension/config patterns | Useful later for IDE-native branch. |
| `sweepai/sweep` | syntax guards, issue/PR automation patterns | targeted module reuse | syntax validation, branch/PR safety patterns | Reuse guards and repo-automation ideas, not full backbone. |
| `OpenInterpreter/open-interpreter` | JSON/tool-call recovery and computer-use patterns | targeted module reuse | parsing/recovery, observation truncation, browser/computer-use patterns | Reuse focused utilities only. |

## Public-template and module-level reuse targets

### A. Terminal coding-agent surface
Primary references:
- `opencode-ai/opencode`
- `OpenHands/OpenHands`
- Aider (existing adopted tool)

Preferred reuse posture:
- use OpenHands for a substantial bounded dev-agent surface,
- use Aider as the tactical editor,
- use OpenCode as a design/code reference for TUI/session/tool/MCP ideas rather than a new backbone.

### B. Context management and change safety
Primary references:
- `plandex-ai/plandex`
- Aider diff/editblock logic
- `sweepai/sweep`

Preferred reuse posture:
- reuse or port robust editblock/search-replace ideas,
- reuse change-set/rollback concepts,
- reuse syntax/guard logic before writing custom fragile patchers.

### C. Tool and connector execution
Primary references:
- `modelcontextprotocol/servers`
- MCP SDKs
- OpenHands tool-execution surface

Preferred reuse posture:
- use official MCP reference servers as starting points,
- wrap them behind local governance and permission controls,
- do not build ad hoc one-off connectors when an MCP-compatible route already exists.

### D. Workflow and long-running automation
Primary references:
- `n8n-io/n8n`
- `Dify`
- `qodo-ai/pr-agent`
- `Significant-Gravitas/AutoGPT` (only later if needed)

Preferred reuse posture:
- use n8n or Dify for workflow/app layers before inventing generic flow builders,
- use PR-Agent for PR review automation before writing first-pass review bots,
- keep long-running agent frameworks deferred unless a bounded need appears.

### E. Document ingestion and advanced RAG
Primary references:
- `microsoft/markitdown`
- `infiniflow/ragflow`
- `HKUDS/RAG-Anything`
- AnythingLLM (already adopted as practical RAG workspace)

Preferred reuse posture:
- use MarkItDown first for broad document-to-markdown conversion,
- use AnythingLLM for practical document chat,
- add RAGFlow or RAG-Anything only when document complexity truly requires it.

## Reuse instructions for coding assistants

### 1. Check this document before designing a subsystem
If the requested capability matches a listed reference implementation, do not default to greenfield code.

### 2. Prefer installable systems over weak clones
If a repo is already a functional installable system and the role is appropriate, prefer installation or bounded integration.

### 3. Prefer targeted module reuse over copy-heavy forks
When only a subsystem is needed, prefer a thin wrapper, port, or integration pattern rather than vendoring large external codebases wholesale.

### 4. Record the chosen posture
Any implementation packet should say which of these modes applies:
- install as product
- wrap and integrate
- reuse module/template
- defer

### 5. Keep external systems subordinate
Reference implementations should not silently become the planning or governance authority.

## Recommended first-wave reuse candidates

These are the highest-value immediate reuse targets for the current platform direction:

1. **OpenHands** — installed/selective bounded dev-agent surface. citeturn675469search1
2. **MarkItDown** — document conversion utility for ingestion pipelines. 
3. **PR-Agent** — PR review/describe automation. citeturn245548search3
4. **n8n** — visual workflow automation layer when workflow breadth justifies it. citeturn245548search5turn245548search0
5. **MCP reference servers** — official thin-tool starting points, with security review because they are documented as reference implementations rather than production-ready solutions. citeturn245548search1
6. **Plandex concepts** — context trimming and rollback/change-set posture.

## Relationship to roadmap items

This document is especially relevant to:
- `RM-GOV-009`
- `RM-UI-005`
- `RM-AUTO-001`
- `RM-INTEL-003`
- `RM-HOME-005`

## Notes

This document is meant to reduce thinking overhead.
Future assistants should use it to decide whether to fork, install, wrap, reuse, defer, or reject a public implementation before writing new code.