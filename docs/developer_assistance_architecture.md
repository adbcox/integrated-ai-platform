# Developer Assistance Architecture

## Role & Boundaries
- Provides a self-hosted, bounded coding agent that stays separate from media_execution while sharing provenance conventions with the broader control plane.
- Treats developer assistance as an advisory subsystem: no automatic commits, no unreviewed shell execution, and every decision surfaces through manifests, queues, or dashboard review items.
- Aligns with the policy and runtime defaults; it does not bypass gates or introduce new execution flows yet.

## Architecture Split & Repo Placement
| Component | Role | Placement | Priority | Notes |
|-----------|------|-----------|----------|-------|
| Ollama | Local inference/runtime layer exposing an OpenAI-compatible HTTP API plus reusable embeddings, powering all coding prompts. | `developer_assistance` branch; core runtime service. | Near-term/core. | Lock versions, log API requests. |
| Open WebUI | Session/UI surface for operators to issue requests, review history, and inspect tool results. | UI surface adjacent to documentation dashboard. | Near-term/core. | Provides session persistence, context inputs, and exposes repository metadata. |
| CodeGemma | First coding model accessed through Ollama, tuned for multi-file edits and reasoning. | Model definition in `developer_assistance/manifests`. | Near-term/core. | Supply example prompts, limit tokens, record responses. |
| Aider | Inspiration for repo mapping, git-aware edits, diff-first confirmation, lint/test loops; not directly integrated yet but informs tool categories and queues. | Reference guidance inside this document. | Near-term/inspiration. | No direct integration; replicate its disciplined loop manually. |
| Continue | Guides CLI/UI dual surface design and configurable toolregistry; influences session/context layering and manifest schema. | Documentation reference. | Mid-term/inspiration. | Focus on maintainable tool definitions and operator controls. |
| OpenHands | Later agentic reference for multi-turn or multi-tool flows; keep as experimental notes for future augmentation. | Flagged in documentation and future roadmap. | Later/experimental. | Do not expand now. |
| MetaGPT | Optional future multi-agent planner to orchestrate complex tasks; only referenced for future phases. | Marked experimental in architecture doc. | Later/optional. | Require explicit gating when introduced. |
| OpenClaw | Explicitly excluded from the first coding path to avoid uncontrolled agentic or risky automation. | Documented exclusion. | N/A | No integration planned in this phase. |

## Agent Loop
1. **User request**: operator opens Open WebUI, selects repo scope, and provides intent.
2. **Context gathering**: system loads `developer_assistance_manifest.json`, repo metadata, and documentation via the tool registry.
3. **Tool selection**: apply Aider-inspired guardrails; read-only utilities (file view, search, diff) are always accessible while write/patch proposals require queueing.
4. **Edit proposal**: CodeGemma via Ollama generates a patch logged in `developer_assistance_sessions.json` with prompt, model, and tool metadata.
5. **Review & diff**: Continue-style panels show the proposed diff; operator approves or rejects before the patch advances.
6. **Governed logging**: entries feed `developer_assistance_review_queue.json` and summary artifacts; readiness noted in `developer_assistance_review_summary.json`.
7. **Optional tooling**: shell commands (lint/test) remain manual, explicitly mentioned in review items, and logged for audit.

## Tool Categories & Risk Levels
| Category | Description | Access | Risk | Manifest Field |
|----------|-------------|--------|------|----------------|
| File read / repo inspection | View file contents, trees. | Always read-only. | Low | `tools.read` |
| Search / docs lookup | Repo-wide search or documentation lookup. | Read-only. | Low | `tools.search` |
| Diff / review | Present candidate diffs for operator review. | Read-only. | Low | `tools.diff` |
| File write / patch proposal | CodeGemma-generated patches. | Gated via review queue. | Medium | `tools.patch` |
| Shell execution | Optional commands (lint/tests) run manually. | Manual approval required. | High | `tools.shell` |
| Optional lint/test execution | Later stage activities, invoked by operator. | Manual & logged. | High | `tools.validation` |

## Artifact Model
- `runtime/developer_assistance_manifest.json`: tool registry, model metadata, gating rules, and reference to Ollama endpoint.
- `runtime/developer_assistance_tool_registry.json`: structured definition of each tool (read-only, patch, shell) plus risk tags.
- `runtime/developer_assistance_sessions.json`: session log (session_id, operator_id, context, prompts, responses, downstream links).
- `runtime/developer_assistance_review_queue.json`: queued edits awaiting notification and review; references session IDs and patch details.
- `runtime/developer_assistance_review_summary.json`: aggregates (open reviews, blocked items, last update) for dashboard consumption.
- `runtime/developer_assistance_recommendations.json`: optional future artifact capturing suggested follow-up actions (test runs, docs updates).

## Provenance & Discovery
- Each artifact records `session_id`, `operator_id`, `timestamp`, `git_head`, `tools_used`, `model_version`, `blocking_reasons`, and `link_target` for the dashboard.
- Search index entries reference these artifacts under `branch` = `developer_assistance` with `link_target` = `/developer-assistance` plus relevant anchors.
- Dashboard surfaces can reuse `base.html` components showing queue counts, session history, and readiness, linking to raw artifacts for audit.

## Phased Plan & Priority
1. **Phase 1 (Next priority)**: Build `developer_assistance_manifest.json` and `developer_assistance_tool_registry.json`; add `/developer-assistance` dashboard route showing tool descriptions and queue counts.
2. **Phase 2**: Populate `developer_assistance_sessions.json` and `developer_assistance_review_queue.json`; connect to CodeGemma via Ollama for patch proposals; expose review summary artifact.
3. **Phase 3**: Introduce lint/test gating, automate `developer_assistance_recommendations.json`, and optionally onboard MetaGPT; keep OpenClaw out of the primary path.

4. **Phase 12 (Execution request queue)**: Introduce the read-only `developer_assistance_execution_requests.json` and `developer_assistance_execution_request_summary.json` artifacts so every approved apply plan, sandbox, and validation expectation is captured for the future bounded execution worker. This keeps the local Codex-like system advisory-only while laying the exact queue contract that the worker will later consume.


## Risks & Exclusions
- Shell commands remain manual; no automation without explicit queue approval.
- Patch proposals stay in the queue until operator confirms—no silent writes.
- Agent sprawl is avoided by sticking to CodeGemma via Ollama for now; OpenHands and MetaGPT remain a future option.
- No auto-commits; operators export approved patches manually.

## Why This Works
- Provides a practical self-hosted alternative to Codex by relying on Ollama + CodeGemma while guided by Aider/Continue best practices.
- Keeps the coding assistant parallel to the media/restoration roadmap, so ongoing enhancement work continues unaffected.
- Next tangible implementation step is the manifest/tool registry and dashboard surface (Phase 1), giving immediate visibility while the rest of the system matures.