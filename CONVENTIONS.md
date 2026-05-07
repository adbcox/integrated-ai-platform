# CONVENTIONS.md
# Aider working conventions for integrated-ai-platform
# Last updated: 2026-05-07 (D-17-XXX LocalAIConfig bootstrap)

## F-Findings Standing Rules

These findings are standing instructions derived from the platform intelligence layer doctrine.
Every Aider session must honor them.

### F22 — Probe Before Assume
**Rule:** Never invent a file path, function name, import, or service endpoint.
Before referencing any path, symbol, or API: read the file or grep for it first.
Fabricating paths that don't exist is a doctrine violation (Finding 22, integration-audit-doctrine.md).

### F25 — Output Hygiene
**Rule:** Agent output must not contain:
- Vault secret values (use hash-only equality: sha256[:12])
- .env values or credential strings
- Internal IP addresses embedded in commit messages
- Bare grep output of /proc/1/environ on credential variables (must pipe through redactor)
Standing instruction: all agent prompts include F25 constraint by default.
Reference: aider-intelligence-doctrine.md Finding 34.

### F6 — Hash-Only Credentials
**Rule:** Credential verification uses hash-only comparison.
Format: `sha256sum <file> | head -c 12` for file comparison.
Never display credential values in tool output, transcripts, or diffs.
Reference: CLAUDE.md "Secrets Management" + aider-verifier-doctrine.md.

## Edit Format
- `--edit-format diff` always (NEVER `--edit-format whole`)
- Reason: whole-file edits on 40+ line files cause truncation failures under load (qwen2.5-coder:7b known issue).
  diff format catches truncation before file is written.

## Source Fidelity — HARD RULE
- Do not invent paths, function names, imports, or type signatures.
- Before editing: read the file to verify the symbol exists and the function signature matches.
- Before referencing a Vault path: check vault/policies/ or existing AppRole config.
- A hallucinated import that compiles is still a doctrine violation.

## Routing Tier Rules
Reference: docs/architecture-facts/work-routing-doctrine.md

| Task class | Route to |
|---|---|
| Mechanical, single-file, deterministic edit | TIER 1: scripts/aider-task.sh (local Aider) |
| Multi-file orchestration (>5 files) | TIER 2: Claude Code / Codex |
| Runtime probes, vault reads, docker exec | TIER 2: Claude Code |
| Novel architecture, security decisions | TIER 2: Claude Code (claude-pro if frontier judgment required) |
| Inference-heavy analysis, synthesis | TIER 2: Claude Code |

## Verification
After any Aider edit:
```bash
pre-commit run --files <changed-file>
python3 -m pytest tests/unit/ -x
```
Layer 1 (bin/aider_guard.py), Layer 1.5 (bin/aider_verifier.py), and Layer 3 (domains/learning.py) run automatically
via scripts/aider-task.sh. Direct `aider` invocations skip these layers — use the wrapper.

## Test Skip Markers
Tests marked `@pytest.mark.skip` with `reason="D-17-131: ..."` are intentionally skipped.
This is NOT a test failure. These 19 tests (priority_engine, dependency_analyzer) are pending
the D-17-132 design decision on tests-vs-production API alignment.
Do not remove skip markers without resolving D-17-132.

## Doctrine References
- docs/architecture-facts/work-routing-doctrine.md — routing tier definitions
- docs/architecture-facts/aider-intelligence-doctrine.md — three-layer guardrail system
- docs/architecture-facts/aider-verifier-doctrine.md — dual-loop verifier (Layer 1.5)
- docs/architecture-facts/codex51-replacement-doctrine.md — Codex vs local Aider decision criteria

## Standing Rules (Platform Scope)
1. 100% open-source, self-hosted stack. The one exception: Proton cloud (email/calendar).
   Do not add external SaaS dependencies without operator approval.
2. This is the "AI workstation" or "platform". The deprecated 7-letter compound term is forbidden
   in all artifacts (code, docs, configs, commit messages, container labels).
3. LLM orchestration surface: Claude Code (this session) = Claude Opus or Sonnet 4.6.
   Execution surface: local Aider = Tier 1 mechanical. No direct Anthropic API in platform services.
4. Model promotion requires artifact evidence. No agent or model is promoted because it "feels better".
   Promotion criteria: docs/architecture-facts/promotion-criteria.md.
5. Vault secrets never appear in diffs, tool output, or transcripts. Hash-only verification always.

## Model Context for Aider Sessions
- Home default: `ollama/qwen3-coder:30b-coding` via Mac Studio (http://192.168.10.142:11434)
- Home upgrade: `ollama/qwen3-coder-next:coding` (same endpoint)
- Home verifier: `ollama/deepseek-coder-v2:16b-lite-instruct-q4_K_M` (bin/aider_verifier.py default; overridable via AIDER_VERIFIER_MODEL env var)
- Travel default: `ollama/qwen2.5-coder:7b` (local 127.0.0.1:11434)
