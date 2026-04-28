# Phase 13.5 — Local Orchestration Smoke Test

**Date**: 2026-04-28
**Hardware**: Mac Mini M4 Pro, 48 GB unified memory
**Ollama**: 0.20.7
**Claude Code**: 2.1.121

## Subagent model probes (Anthropic-compatible endpoint)

`POST http://localhost:11434/v1/messages` with `anthropic-version: 2023-06-01`.

| Subagent (model) | Wall-clock | Response |
|---|---|---|
| decomposer (qwen2.5-coder:32b) | 7s | `OK` |
| implementer (qwen2.5-coder:14b) | 5s | `OK` |
| reviewer (qwen2.5-coder:7b) | 3s | `OK` |

All three subagents reachable through the Anthropic-compatible interface that
Claude Code uses when running under `claude-local`.

## litellm-gateway model surface (post-S6.1)

`GET http://localhost:4000/v1/models` returns:

```
qwen-coder-32b
qwen-coder-14b
qwen-coder-7b
devstral
deepseek-coder
```

No `claude-*`, no `gpt-*`. All routes are `ollama/<name>` against
`http://host.docker.internal:11434`.

## Subagent frontmatter validation

All three agent files in `~/.claude/agents/` parse as valid YAML frontmatter
with the expected `name`, `description`, `tools`, `model` keys. Models pinned
explicitly in spec rather than relying on a default.

## Conclusion

Orchestrator chain is reachable end-to-end. Each tier (decomposer 32b →
implementer 14b → reviewer 7b) responds in single-digit seconds for trivial
prompts. Decomposition-class wall-clock previously measured at 70s (32b) and
43s (14b) per `baseline.md` — those numbers stand.

Platform LLM dependency is now exclusively local Ollama. Anthropic Pro
subscription access remains available to the human operator via the
`claude-pro` shell function but does not flow through any platform service.
