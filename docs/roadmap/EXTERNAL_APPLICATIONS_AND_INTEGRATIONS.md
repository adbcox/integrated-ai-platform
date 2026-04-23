# External Applications and Integration Catalog

## Purpose

This document is the running catalog of external applications, services, standards, and tooling that the integrated AI platform will adopt, integrate with, or interface against.

It exists to solve four problems:

1. keep a single visible list of external systems that must be installed or connected
2. preserve official download, source, and API references in one place
3. make phase placement and ownership explicit
4. prevent repeated loss of adoption/integration research across roadmap revisions

## Canonical use

Use this document as the roadmap-facing catalog for external systems.

- Roadmap items remain the execution/governance units.
- This catalog is the cross-cutting external-systems reference.
- Every external system used by the platform should appear here once it is approved, conditionally approved, or under active consideration.
- The platform should prefer one governing external-connectivity model rather than per-app ad hoc integrations.
- For local AI tool role decisions, also read:
  - `docs/architecture/LOCAL_AI_STACK_ROLE_MATRIX.md`

## Status values

- `Adopt` — approved external system to bring in
- `Hybrid` — external system plus repo-owned wrapper/adapter/policy layer
- `Conditional` — only adopt if later evidence justifies it
- `Reference only` — informative or optional external surface, not a core dependency
- `Unresolved` — named in planning, but still needs verification or final decision
- `Reject-current-core` — do not use as a current core-stack choice

## External connectivity architecture rule

External systems should not be integrated one by one with independent auth, sync, polling, webhook, and error-handling logic.

Instead, the platform should converge toward one **external application connectivity and integration control plane** with:

- standardized adapter boundaries
- centralized auth posture and credential reference rules
- standard sync modes such as polling, push, webhook, and event normalization
- capability registration for each connector
- health/error visibility for external integrations
- local policy and orchestration on top of external capabilities

This is now tracked as:

- `RM-GOV-009` — external application connectivity and integration control plane

## Local AI stack role matrix summary

This section is the quick operational view of the preferred local AI stack.

| Stack role | Primary choice | Secondary / optional | Current posture | Notes |
|---|---|---|---|---|
| Local model runtime | Ollama | LM Studio on select hosts; LocalAI only when compatibility needs are real | Adopt | Keep runtime simple and local-first |
| Local coding execution | Aider + Ollama | OpenHands | Adopt | Governed local coding path stays primary |
| General local chat UI | Open WebUI | LM Studio UI | Adopt | One primary local chat surface |
| Document/RAG workspace | AnythingLLM | RAGFlow | Adopt / selective | Practical document workflows first |
| Workflow / AI app builder | Dify | none by default | Adopt / selective | Workflow layer, not architecture authority |
| Home / voice automation anchor | Home Assistant Assist | Whisper later where justified | Adopt | Preferred local home voice anchor |
| API compatibility bridge | none by default | LocalAI | Conditional | Add only when compatibility need is real |
| Messaging / assistant gateway | none by default | OpenClaw | Conditional / later | Evaluate later as its own subsystem |
| Fine-tuning / training stack | none by default | LLaMA-Factory | Conditional / later | Not current priority |
| Multi-agent framework | none by default | CrewAI / AutoGen | Conditional / later | Not foundational now |

## Core catalog

| System | Domain group | Decision | Phase / group | Install required | Primary role | Official source / download | API / integration docs | Integration pattern | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Ollama | Runtime / models | Adopt | Phase 1 and continuing local stack baseline | Yes | Default local model manager and primary runtime | https://github.com/ollama/ollama | https://github.com/ollama/ollama | Repo-owned inference gateway in front | Default local route; primary current runtime choice |
| LM Studio | Runtime / local serving | Conditional / selective adopt | Later host-specific enhancement | Yes if selected | Desktop/server local model serving alternative | https://lmstudio.ai/ | https://lmstudio.ai/docs/developer/core/server | Host-specific local server or GUI-first serving layer | Useful where GUI/server fit beats default Ollama-only posture |
| LocalAI | Runtime / compatibility API | Conditional / selective adopt | Later compatibility bridge if justified | Yes if selected | OpenAI-compatible local API bridge and broader local inference surface | https://localai.io/ | https://localai.io/docs/overview/ | Only adopt if real compatibility or multimodal breadth justifies overlap | Do not add by default alongside Ollama without a bounded reason |
| Open WebUI | Local chat UI | Adopt | Near-term local AI stack | Yes | Primary local conversational UI | https://openwebui.com/ | https://docs.openwebui.com/ | Self-hosted UI over approved local runtimes | Preferred current general local chat surface |
| AnythingLLM | RAG / document workspace | Adopt | Near-term local AI stack | Yes | Primary practical local document/RAG workspace | https://anythingllm.com/ | https://docs.anythingllm.com/ | Local documents, agent and connector-assisted knowledge workflows | Preferred practical document interaction surface |
| RAGFlow | RAG / document understanding | Conditional / selective adopt | Later document-heavy branch if needed | Yes if selected | Advanced document understanding and heavier RAG | https://github.com/infiniflow/ragflow | https://github.com/infiniflow/ragflow | Adopt only when document extraction quality is a real bottleneck | Not default alongside AnythingLLM |
| Dify | Workflow / AI apps | Conditional / selective adopt | Later workflow layer | Yes if selected | Low-code AI workflow and application builder | https://dify.ai/ | https://docs.dify.ai/en/guides/workspace/app | Workflow/app layer above governed platform | Must not become planning authority |
| OpenHands | Runtime / tools | Hybrid | Phase 2 and dev surface support | Yes if selected | Selective dev-agent surface and monitoring interface | https://openhands.dev/ | https://docs.openhands.dev/ | Governed execution surface subordinate to local control plane | Useful but never the planning authority |
| Home Assistant Assist | Home / voice | Adopt | Home branch | Yes via Home Assistant posture | Primary local home / voice automation anchor | https://www.home-assistant.io/ | https://developers.home-assistant.io/docs/voice/pipelines/ | Home/device bridge and local voice anchor | Preferred home voice path |
| Aider RepoMap / edit workflows | Developer assistant | Hybrid | Phase 3 / Phase 6 adapter | No separate service required | Repo map and edit primitive | https://aider.chat/docs/repomap.html | https://aider.chat/docs/repomap.html | Adapter behind shared runtime | Strong fit for repo understanding; never the backbone |
| vLLM | Runtime / models | Adopt | Phase 1-2 optional | Yes | Heavier shared inference / benchmark backend | https://github.com/vllm-project/vllm | https://github.com/vllm-project/vllm | Optional backend behind internal gateway | Must not replace Ollama as default |
| OpenHands Software Agent SDK | Runtime / tools | Hybrid | Phase 2 | Yes if selected | Tool/workspace model patterns or selective components | https://github.com/OpenHands/software-agent-sdk | https://github.com/OpenHands/software-agent-sdk | Adopt concepts/components behind local contracts | Do not replace existing control plane |
| Model Context Protocol (MCP) | Tool interoperability | Adopt | Phase 2 | Protocol / libraries | Standard external tool boundary | https://github.com/modelcontextprotocol/modelcontextprotocol | https://github.com/modelcontextprotocol/modelcontextprotocol | Use as default external tool boundary | Avoid one-off ad hoc tool integrations |
| Qdrant | Retrieval / memory | Adopt | Phase 2-4 | Yes | Semantic memory and vector retrieval | https://github.com/qdrant/qdrant | https://github.com/qdrant/qdrant | Service behind repo-owned retrieval logic | Do not build custom vector DB |
| gVisor | Sandbox / isolation | Adopt | Phase 2 | Yes | First-line sandbox execution | https://gvisor.dev/ | https://gvisor.dev/ | Execution isolation under local contracts | Lower-friction starting point |
| Firecracker | Sandbox / isolation | Conditional | Phase 6+ only if needed | Yes if selected | Stronger isolation tier | https://github.com/firecracker-microvm/firecracker | https://github.com/firecracker-microvm/firecracker | Optional later hardening | Evidence-gated; not early default |
| SWE-bench | Benchmarking | Adopt | Phase 3-5 | Yes | Public benchmark harness | https://github.com/SWE-bench/SWE-bench | https://github.com/SWE-bench/SWE-bench | Public harness plus repo-local wrappers | Avoid bespoke benchmark runner |
| Backstage | Catalog / portal | Adopt | Phase 5 pilot | Yes | Developer portal and software catalog | https://github.com/backstage/backstage | https://github.com/backstage/backstage | External app plus repo-owned usage model | Only after core runtime is stable |
| GLPI | CMDB | Adopt | Phase 5 | Yes | Default authoritative CMDB | https://github.com/glpi-project/docker-images | https://help.glpi-project.org/documentation/modules/configuration/general/api/restful-api-v2 | Read-only first; integrate via API | Default CMDB recommendation |
| CloudQuery | Inventory enrichment | Hybrid | Phase 5 optional | Yes if selected | Read-only cloud / infra enrichment | https://github.com/cloudquery/cloudquery | https://github.com/cloudquery/cloudquery | Enrichment around authoritative CMDB | Not sole source of truth |
| i-doit | CMDB alternative | Conditional | Phase 5 decision only if needed | Yes if selected | ITIL-heavy relationship modeling | https://www.i-doit.com/ | https://kb.i-doit.com/en/i-doit-add-ons/api/index.html | Alternative CMDB path only | Not default recommendation |
| Temporal | Workflow backbone | Conditional | Phase 6+ only if needed | Yes if selected | Durable workflow/orchestration | https://github.com/temporalio/temporal | https://github.com/temporalio/temporal | Only if current manager proves insufficient | Do not replatform early |
| Plane | Roadmap operations | Adopt | Governance rollout after GOV-006 / GOV-007 | Yes | Operational planning / execution layer | https://plane.so/self-hosted | https://developers.plane.so/api-reference/introduction | Hybrid with repo-doc canonical roadmap | Repo docs remain canonical |
| OpenClaw | Messaging / assistant gateway | Conditional | Later evaluation | Yes if selected | Messaging-channel gateway candidate | https://github.com/openclaw/openclaw | https://github.com/openclaw/openclaw | Evaluate later as a subsystem, not default core stack | Too large to add casually |
| CrewAI | Agent framework | Conditional | Later experiments only | Yes if selected | Multi-agent orchestration framework | https://www.crewai.com/ | https://www.crewai.com/ | Defer until bounded need exists | Not foundational now |
| AutoGen | Agent framework | Conditional | Later experiments only | Yes if selected | Multi-agent orchestration framework | https://microsoft.github.io/autogen/ | https://microsoft.github.io/autogen/ | Defer until bounded need exists | Not foundational now |
| LLaMA-Factory | Fine-tuning / training | Conditional | Later fine-tuning track only | Yes if selected | Fine-tuning and training surface | https://github.com/hiyouga/LLaMA-Factory | https://github.com/hiyouga/LLaMA-Factory | Use only if formal fine-tuning track begins | Not current priority |
| Libra Chat | Local chat UI | Reject-current-core | N/A | No | Overlapping chat UI surface | https://github.com/topics/open-source-ai | TBD | Do not adopt as core current stack choice | Open WebUI already fills this role |
| BrowserOS | Browser / agent surface | Reject-current-core | N/A | No | Overlapping browser/agent surface | https://github.com/topics/open-source-ai | TBD | Do not adopt as core current stack choice | Overlaps with browser/computer-use branches |
| ADeus | Specialized assistant / wearable | Reject-current-core | N/A | No | Specialized wearable assistant surface | https://github.com/topics/open-source-ai | TBD | Do not adopt as core current stack choice | Too specialized for core stack |

## Media systems

| System | Domain group | Decision | Phase / group | Install required | Primary role | Official source / download | API / integration docs | Integration pattern | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Plex Media Server / Plex apps | Media control | Adopt / integrate | Media branch | Yes | Personal media server and playback ecosystem | https://support.plex.tv/articles/200288286-what-is-plex/ | https://support.plex.tv/articles/200288286-what-is-plex/ | Dashboard, endpoint compliance, watchlist-aware orchestration | Major external media surface |
| Sonarr | Media automation | Adopt / integrate | Media branch | Yes | TV acquisition / series management | https://sonarr.tv/docs/ | https://sonarr.tv/docs/api/ | Dashboard requests, watchlist routing, status tracking | External app; do not rebuild |
| Radarr | Media automation | Adopt / integrate | Media branch | Yes | Movie acquisition / library management | https://radarr.video/ | https://radarr.video/docs/api/ | Dashboard requests, watchlist routing, status tracking | External app; do not rebuild |
| Prowlarr | Media automation | Adopt / integrate | Media branch | Yes | Indexer manager / proxy for *arr stack | https://prowlarr.com/docs/ | https://prowlarr.com/docs/api/ | Upstream media-indexer layer for *arr integrations | Strong likely companion to Sonarr/Radarr |
| NVIDIA Shield endpoints | Media endpoints | Integrate | Media monitoring branch | Existing hardware | Playback endpoint monitoring / compliance | https://support.plex.tv/articles/200288286-what-is-plex/ | Device-specific APIs vary | Inventory + endpoint compliance + Plex profile validation | Treated as managed endpoint, not app dependency |
| Samsung TV endpoints | Media endpoints | Integrate | Media monitoring branch | Existing hardware | Playback endpoint monitoring / compliance | https://support.plex.tv/articles/200288286-what-is-plex/ | Device-specific APIs vary | Inventory + endpoint compliance + Plex profile validation | Managed endpoint class |
| Apple TV endpoints | Media endpoints | Integrate | Media monitoring branch | Existing hardware | Playback endpoint monitoring / compliance | https://support.plex.tv/articles/200288286-what-is-plex/ | Device-specific APIs vary | Inventory + endpoint compliance + Plex profile validation | Managed endpoint class |
| Netflix | Streaming / data source | Reference only / unresolved integration posture | Later media intelligence branch | App/service external | External catalog/content source reference only for now | https://about.netflix.com/en/newsroom | No public official general integration API verified | Treat as content/source reference until a lawful supported integration path is confirmed | Do not assume official automation API exists |

## Home and environment systems

| System | Domain group | Decision | Phase / group | Install required | Primary role | Official source / download | API / integration docs | Integration pattern | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Home Assistant | Home / automation | Adopt / integrate | Home branch | Yes | Device bridge for home/environment systems | https://www.home-assistant.io/ | https://developers.home-assistant.io/docs/api/rest and https://developers.home-assistant.io/docs/api/websocket | Use HA for device/entity control; keep reporting and policy in this system | Central external home-automation surface |
| Air quality sensors / purifier integrations | Home / environment | Integrate via Home Assistant | Home branch | Existing hardware + HA integrations | Indoor environment sensing and automation | https://www.home-assistant.io/ | https://developers.home-assistant.io/docs/api/rest and https://developers.home-assistant.io/docs/api/websocket | HA as bridge; local dashboard/reporting owned here | Room-level control/reporting pattern |
| TP-Link Deco / network telemetry | Home / network | Integrate where feasible | Ops / home networking branch | Existing hardware | Network telemetry / alerts | Vendor-specific | Home Assistant and vendor patterns where available | Prefer HA or standard telemetry before custom work | Coverage may vary by model |

## Health and athlete systems

| System | Domain group | Decision | Phase / group | Install required | Primary role | Official source / download | API / integration docs | Integration pattern | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Strava | Athlete analytics | Integrate | Athlete analytics branch | App/service external | Activity ingest, summaries, advisory flows | https://developers.strava.com/ | https://developers.strava.com/docs/ and https://developers.strava.com/docs/reference/ | OAuth app + API/webhooks | External athlete-data source |
| “Sportster” | Athlete analytics | Unresolved | Athlete analytics branch | Unknown | Named in planning, but not yet verified | TBD | TBD | Hold until exact product/app is confirmed | Do not assume spelling or product identity |

## AI and coding surfaces

| System | Domain group | Decision | Phase / group | Install required | Primary role | Official source / download | API / integration docs | Integration pattern | Notes |
|---|---|---|---|---|---|---|---|---|---|
| ChatGPT desktop / OpenAI API | AI surface | Integrate / reference | Developer and planning workflows | App and/or API | Chat interface, desktop workflow, API access | https://openai.com/chatgpt/desktop/ and https://platform.openai.com/docs/quickstart | https://platform.openai.com/docs/quickstart | Human workflow tool and optional API-backed integration | External AI surface, not the local default engine |
| Claude Code | AI coding surface | Controlled adapter / reference | Controlled adapters phase | Yes if used | Supervisory coding path and optional adapter | https://docs.anthropic.com/en/docs/claude-code/overview | https://docs.anthropic.com/en/docs/claude-code/getting-started | Controlled adapter behind shared runtime where possible | Must not become default backbone |

## Market comparison and category-reference apps

These are primarily reference applications used to track market expectations, identify possible future integrations, and clarify where the platform should integrate instead of rebuild. They are **not** the architecture backbone and should not override the local-first control-plane/runtime direction.

| System | Domain group | Decision | Phase / group | Install required | Primary role | Official source / download | API / integration docs | Integration pattern | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Perplexity | Research / assistant | Reference only | Market comparison layer | External app/service | Research/search product-category reference | https://www.perplexity.ai/ | Public API/docs only if later justified | Compare category expectations; do not use as backbone | Useful for research UX reference |
| Granola | Meeting notes | Reference only | Market comparison layer | External app/service | Meeting-note / transcript formatting reference | https://www.granola.ai/ | Verify later if integration is ever desired | Category reference only | Useful for meetings branch benchmarking |
| Wispr Flow | Dictation / voice | Reference only | Market comparison layer | External app/service | Voice dictation product-category reference | https://wisprflow.ai/ | Verify later if integration is ever desired | Category reference only | Useful for voice-input expectations |
| Gamma | Presentation / doc generation | Reference only | Market comparison layer | External app/service | Generated-doc / deck product-category reference | https://gamma.app/ | Verify later if integration is ever desired | Category reference only | Useful for generated-output expectations |
| NotebookLM | Knowledge / document transformation | Reference only | Market comparison layer | External app/service | Knowledge-product comparison surface | https://notebooklm.google/ | Verify later if integration is ever desired | Category reference only | Useful for document/audio transformation reference |
| Cursor | Coding assistant | Reference only | Competitive coding comparison | External app/service | Coding product-category comparison | https://www.cursor.com/ | No backbone use | Competitive/comparison reference only | Compare UX/coding expectations only |
| Replit | App-building / agentic coding | Reference only | Competitive app-building comparison | External app/service | Natural-language app-building comparison | https://replit.com/ | No backbone use | Competitive/comparison reference only | Compare productization patterns only |
| Codeium | Coding assistant | Reference only | Competitive coding comparison | External app/service | Coding-autocomplete comparison | https://codeium.com/ | No backbone use | Competitive/comparison reference only | Comparison set only |
| Lindy | Workflow automation | Reference only | Market comparison layer | External app/service | Workflow-agent category reference | https://www.lindy.ai/ | Verify later if integration is ever desired | Category reference only | Helps benchmark workflow-agent UX |
| ElevenLabs | Voice / speech | Reference only | Future creative/voice branch | External app/service | Voice synthesis comparison/reference | https://elevenlabs.io/ | Verify later if integration is ever desired | Category reference only | Use only if later branch needs justify it |

## Integration pattern guidance

Use these default patterns when deciding how to bring in an external system:

- **Adopt** when the system is strong commodity infrastructure and does not threaten platform sovereignty
- **Hybrid** when the system is useful but must sit behind a repo-owned adapter, wrapper, policy layer, or orchestration boundary
- **Reference only** when the system is primarily a benchmark, market comparison, or future possibility
- **Conditional** when adoption should be evidence-gated and deferred until core runtime maturity justifies it
- **Reject-current-core** when the system is intentionally not part of the current default stack because a clearer role owner already exists

## Rules for any new external system

Before adding a new external application here, capture:

- official product/repository URL
- download / install path if applicable
- official API / integration docs if they exist
- adopt / hybrid / conditional / reference-only / reject-current-core decision
- intended roadmap phase or group
- local wrapper / adapter plan
- authentication model
- licensing notes if material
- removability / rollback strategy

## Immediate follow-up tasks

1. keep the local AI stack role matrix synchronized with `LOCAL_AI_STACK_ROLE_MATRIX.md`
2. expand media section with exact Plex watchlist/discover integration decisions
3. confirm whether Prowlarr should be formalized as a first-class media dependency
4. resolve the exact identity of “Sportster” if it is still intended
5. add per-system version pinning and local deployment notes after approval
6. link each external system to the relevant roadmap item IDs once item-level normalization is complete
7. use `RM-GOV-009` to define the standard integration-control-plane model before broadening one-off external adapters
