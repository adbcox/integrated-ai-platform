# Local AI Stack Role Matrix

## Purpose

This document defines the preferred local AI stack for the integrated AI platform.

It exists to prevent a common failure mode:
- installing many overlapping open-source AI systems without clear role boundaries,
- forcing future coding assistants to re-derive stack choices,
- wasting tokens and time on stack reconsideration instead of execution.

This document should be treated as the **default local AI stack role and adoption policy** unless future repo truth deliberately changes it.

## Core rule

Do not adopt multiple tools for the same role without a specific documented reason.

For each stack role, prefer:
- one primary choice
- one optional/secondary choice where justified
- explicit defer or reject posture for overlapping alternatives

## Stack-role matrix

| Stack role | Primary choice | Secondary / optional | Current posture | Why |
|---|---|---|---|---|
| Local model runtime | Ollama | LM Studio on select hosts; LocalAI only when compatibility needs are real | adopt | Keep runtime simple and local-first |
| Local coding execution | Aider + Ollama | OpenHands for longer interactive dev-agent sessions | adopt | Keep governed local coding path primary |
| General local chat UI | Open WebUI | LM Studio UI on single-host desktop setups | adopt | Provide ChatGPT-style local interface without changing governance backbone |
| Document/RAG workspace | AnythingLLM | RAGFlow for heavier document understanding needs | adopt-selective | Practical doc chat first; heavier document parsing only if needed |
| Workflow / AI app builder | Dify | none by default | adopt-selective | Good workflow layer, but not the system’s planning authority |
| Home / voice automation anchor | Home Assistant Assist | Whisper later where specific transcription needs justify it | adopt | Best-fit local home voice and device bridge |
| API compatibility bridge | none by default | LocalAI when software compatibility or multimodal API breadth is needed | defer-selective | Avoid duplicate local API stacks unless justified |
| Messaging / assistant gateway | none by default | OpenClaw as later candidate | defer | Candidate only after connector and ingress posture are stable |
| Fine-tuning / training stack | none by default | LLaMA-Factory later if formal fine-tuning track begins | defer | Not current priority |
| Multi-agent framework | none by default | CrewAI / AutoGen later for bounded experiments | defer | Not foundational to current system |
| Media / specialized local AI | adopt by branch only | Whisper, Immich, Stable Diffusion | branch-specific | Do not let domain tools become the core stack |

## Adoption / reject / defer table

### Adopt now

#### Ollama
- role: primary local model runtime
- posture: `adopt`
- notes: default local runtime and primary local model manager

#### Open WebUI
- role: primary general local chat UI
- posture: `adopt`
- notes: user-facing interface over approved local or compatible backends

#### AnythingLLM
- role: primary practical document/RAG workspace
- posture: `adopt`
- notes: use for local documents, RAG, and connector-assisted knowledge workflows

#### Home Assistant Assist
- role: primary home / voice automation anchor
- posture: `adopt`
- notes: preferred local voice and home-device bridge

### Adopt selectively

#### Aider
- role: primary local coding executor
- posture: `adopt`
- notes: remains the tactical execution engine for bounded coding tasks

#### OpenHands
- role: bounded dev-agent surface
- posture: `adopt-selective`
- notes: useful for longer interactive dev sessions; must remain subordinate to governed execution rules

#### LM Studio
- role: desktop local server / GUI alternative
- posture: `adopt-selective`
- notes: use where GUI-first local serving or host-specific fit is stronger than Ollama alone

#### Dify
- role: workflow / AI application builder
- posture: `adopt-selective`
- notes: useful as a workflow layer above the governed substrate, not instead of it

#### RAGFlow
- role: advanced document understanding / heavier RAG option
- posture: `adopt-selective`
- notes: only when document extraction or retrieval quality is the real bottleneck

#### LocalAI
- role: optional compatibility API bridge
- posture: `adopt-selective`
- notes: only when real compatibility or multimodal needs justify the overlap with Ollama/LM Studio

### Defer

#### OpenClaw
- role: possible messaging / assistant gateway
- posture: `defer`
- notes: strong later candidate, but too large to drop into the current backbone casually

#### LLaMA-Factory
- role: fine-tuning / training
- posture: `defer`
- notes: only after the system formally starts a local fine-tuning track

#### CrewAI
- role: multi-agent orchestration framework
- posture: `defer`
- notes: not a current foundational need

#### AutoGen
- role: multi-agent orchestration framework
- posture: `defer`
- notes: not a current foundational need

#### Nextcloud Hub AI
- role: private office/knowledge adjunct
- posture: `defer`
- notes: useful later, not core to the present AI stack

### Reject for current core stack

#### Libra Chat
- role: overlapping local chat UI
- posture: `reject-current-core`
- notes: no need to add another primary chat surface while Open WebUI already fills the role

#### BrowserOS
- role: overlapping browser/agent/browser-automation surface
- posture: `reject-current-core`
- notes: insufficiently justified for the core stack and overlaps with browser/computer-use branches

#### ADeus
- role: specialized wearable assistant
- posture: `reject-current-core`
- notes: too specialized for the current core-platform stack

## Role rules for coding assistants

### 1. Runtime selection
Default to Ollama unless the repo explicitly says a host or task should use LM Studio or LocalAI.

### 2. UI selection
Default to Open WebUI for a general local conversational interface.
Do not propose multiple overlapping general chat UIs without a bounded reason.

### 3. RAG / document system selection
Default to AnythingLLM for practical local document interaction.
Escalate to RAGFlow only if document extraction and understanding quality is the real limiting factor.

### 4. Workflow layer selection
Treat Dify as a workflow/app layer candidate, not as the architecture or planning authority.

### 5. Home and voice
Treat Home Assistant Assist as the preferred home/voice anchor.

### 6. Development and coding
Treat Aider as the primary local tactical executor.
Treat OpenHands as optional and subordinate.

## Duplication-avoidance rules

Do not adopt both as primary defaults in the same role without explicit justification:
- Ollama and LocalAI
- Open WebUI and Libra Chat
- AnythingLLM and RAGFlow
- Aider and OpenHands
- Dify and agent-framework-heavy orchestration tools

## Relationship to roadmap items

This document is especially relevant to:
- `RM-GOV-009`
- `RM-UI-005`
- `RM-HOME-005`
- `RM-AUTO-001`
- `RM-INTEL-003`

## Notes

This matrix is designed to reduce assistant thinking overhead.
If a future assistant needs to choose a local AI stack tool, it should start here rather than rebuilding the decision from scratch.
