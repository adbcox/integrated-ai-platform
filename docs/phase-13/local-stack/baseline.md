# Local Stack Performance Baseline

**Date**: 2026-04-28
**Hardware**: Mac Mini M4 Pro, 48 GB unified memory
**Ollama version**: 0.20.7

## Smoke test (trivial prompt)

| Model | Size | Load (cold) | Eval | Response |
|---|---|---|---|---|
| qwen2.5-coder:32b | 19 GB | 11.4s | 0.1s | "ok" |
| qwen2.5-coder:14b | 9.0 GB | 4.4s | 0.0s | "Ok" |
| qwen2.5-coder:7b | 4.7 GB | 2.7s | 0.0s | "Ok" |

## Decomposition-class prompt (multi-paragraph spec request)

| Model | Wall-clock |
|---|---|
| qwen2.5-coder:32b | 70s |
| qwen2.5-coder:14b | 43s |

## Anthropic-compatible endpoint

`POST http://localhost:11434/v1/messages` with `anthropic-version: 2023-06-01`
returns valid Anthropic-format response. ✅ Substrate ready for `claude-local`.

## Operational notes

- 48 GB RAM accommodates ANY single model (32b, 14b, 7b). Ollama auto-loads/unloads on model switch — subagent handoffs incur load latency on each swap.
- 32b orchestrator at ~70s for decomposition is acceptable for planning steps but not interactive-snappy. Use intentionally, not as default-on-every-prompt.
- Mitigation if memory pressure becomes operational: drop to 14b orchestrator + 7b implementer. Subagent frontmatter would need updating at that point.
