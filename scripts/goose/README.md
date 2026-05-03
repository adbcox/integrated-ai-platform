# scripts/goose/ — Goose CLI launchers (D-17-13)

Goose CLI (Block, Apache 2.0) is one of the platform's execution surfaces
alongside Claude Code and Codex. This directory holds path-specific
launcher scripts.

## Current path (D-17-13 reopened, 2026-05-03)

**No launcher needed.** Invoke `goose` directly. Provider/model/host
are read from `~/.config/goose/config.yaml` at startup:

```yaml
GOOSE_PROVIDER: "ollama"
GOOSE_MODEL:    "qwen3-coder:30b"
OLLAMA_HOST:    "http://mac-studio.internal:11434"
```

The repo-tracked source-of-truth for that file is
`config/goose/config.yaml` (operator workflow: edit repo file, then
`cp config/goose/config.yaml ~/.config/goose/config.yaml`).

## Capability boundary

The capability-validation phase disables `developer` (shell exec +
file write), `summon`, `apps`, `chatrecall`, `summarize`, `tom`,
`code_execution`, `orchestrator` extensions. Read-only via
`filesystem-mcp` and `xindex` only. Operator review is mandatory on
all output.

Full posture + Phase-A promotion gate documented in
`docs/architecture-facts/goose-capability-boundary.md`.

## Historical paths

### `goose-via-litellm-historical.sh` — OBSOLETED 2026-05-03

The original D-17-13 path routed Goose's `openai` provider through
the platform `litellm-gateway` (host port 4000), which required reading
the litellm master key from Vault and exporting it as `OPENAI_API_KEY`.

That path was retired when D-17-13 reopened on the F1 unblocker
(D-17-12 found qwen3-coder:30b emits structured `tool_calls` via Ollama
0.22.1 in streaming mode — F1.B). Going direct to Mac Studio Ollama
removes a network hop and the Vault credential surface entirely.

Preserved verbatim for historical reference until next phase rollover.
