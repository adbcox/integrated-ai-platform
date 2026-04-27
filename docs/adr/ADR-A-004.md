# ADR-A-004 — Local LLM strategy: Ollama with 6-model fleet
**Status:** Accepted
**Date:** 2026-04-20
**Source:** Phase 5 local LLM deployment

## Context

The platform requires LLM inference for: autonomous code modification (aider), embedding generation (RAG pipeline), general chat (Open WebUI), and fast structured output (agent decision layers). Cloud-only inference introduces latency, cost, and data-egress concerns for a self-hosted platform. On-device inference on M4 Pro (64 GB unified memory) is feasible for models up to ~70B quantised.

## Decision

Run Ollama as the local inference server hosting a 6-model fleet (total ~57 GB):
- **qwen2.5-coder:32b** — primary code generation and aider backend
- **qwen2.5-coder:7b** — fast code generation, decomposition subtasks
- **llama3.3:70b** — general reasoning and long-context tasks
- **deepseek-r1:32b** — chain-of-thought and planning
- **nomic-embed-text** — RAG embeddings (768-dim)
- **mxbai-embed-large** — secondary embeddings for cross-encoder reranking

LiteLLM Gateway provides a unified OpenAI-compatible API in front of Ollama, enabling model aliasing and fallback routing.

## Consequences

- 57 GB of model weights are resident on the Mac Mini; adding models requires verifying available VRAM/unified memory headroom
- qwen2.5-coder:7b truncates whole-file responses on files >40 lines under load; decomposition targets new files <20 lines to work around this
- LiteLLM Gateway is a required dependency for the autonomous executor — if it is down, aider falls back to cloud (Claude Sonnet via API key)
- Ollama must be running before Open WebUI, LiteLLM, and aider start; systemd/launchd ordering matters
- Cloud fallback (Claude API) is intentionally retained for tasks that exceed local model quality thresholds
