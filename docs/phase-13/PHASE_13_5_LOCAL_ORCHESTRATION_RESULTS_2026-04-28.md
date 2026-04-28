# Phase 13.5 — Local Orchestration Architecture — Closing Report

**Date**: 2026-04-28
**Status**: COMPLETE — all sections executed, regression probe clean, single
commit covers the full phase.

## Goal

Restructure the platform's LLM access so that:

1. The default coding-assistant chain runs entirely on local Ollama (Mac
   Mini M4 Pro, qwen-coder family).
2. The Anthropic Pro subscription remains available for high-judgment work
   via a separate, explicit shell mode.
3. Platform services are decoupled from any cloud-LLM availability or
   quota constraint.

## Sections executed

### §1 — Decisions captured

Master directives, all confirmed:

- Subagent model assignment: decomposer = qwen2.5-coder:32b,
  implementer = qwen2.5-coder:14b, reviewer = qwen2.5-coder:7b
- Keep extra Ollama models on disk (devstral, deepseek-coder-v2) as
  experimentation surface
- `alwaysThinkingEnabled: false` in settings.json
- Do **not** pin model in settings.json — would break `claude-pro`
  (would pass an Ollama-only model name to Anthropic)

### §2 — Performance baseline

`docs/phase-13/local-stack/baseline.md`. Smoke prompts and
decomposition-class prompts measured for all three models. 32b orchestrator
wall-clock for a real decomposition prompt: 70s. 14b: 43s. Operationally:
acceptable for planning, not interactive-snappy.

### §3 — Shell functions

Appended to `~/.zshrc`:

```
claude-local() {
  ANTHROPIC_BASE_URL=http://localhost:11434 \
  ANTHROPIC_AUTH_TOKEN=ollama \
  command claude --model "qwen2.5-coder:32b" "$@"
}

claude-pro() {
  unset ANTHROPIC_BASE_URL ANTHROPIC_AUTH_TOKEN
  command claude "$@"
}

alias claude=claude-local
```

CLAUDE.md "LLM Access Doctrine" section documents the modes, the
recommended split (`claude-local` for routine work, `claude-pro` for
high-judgment), and the rule that platform services NEVER depend on
Anthropic API access.

### §4 — Subagent specs

`~/.claude/agents/{decomposer,implementer,reviewer}.md` created with
explicit `model:` pins (so the chain works under `claude-local` against
the Anthropic-compatible Ollama endpoint, and under `claude-pro` it
falls back to Anthropic-default model — the spec only takes effect when
the requested model is reachable).

### §5 — Settings

`~/.claude/settings.json` now contains `alwaysThinkingEnabled: false`
plus the `env` block (DISABLE_AUTOUPDATER, CLAUDE_CODE_DISABLE_1M_CONTEXT,
CLAUDE_CODE_AUTO_COMPACT_WINDOW). Model **not** pinned per master
direction. JSON validates clean.

### §6 — Platform integration

- **S6.1**: `litellm_config.yaml` — removed `claude-sonnet`,
  `claude-haiku` model blocks. `vault-agent-litellm/credentials.env.tmpl`
  — removed ANTHROPIC_API_KEY render block (now renders only
  LITELLM_MASTER_KEY). `litellm-gateway-policy.hcl` — removed
  `secret/data/anthropic/api` path; reloaded into Vault. Recreated
  `litellm-gateway` container; `/v1/models` returns
  `qwen-coder-32b/14b/7b, devstral, deepseek-coder` only.
- **S6.2**: `vault kv metadata delete secret/anthropic/api` — path no
  longer listed under `secret/`.
- **S6.3**: Open-WebUI verified via env inspection: only
  OpenAI-compatible upstream is `http://litellm-gateway:4000/v1`. No
  `ANTHROPIC_*` or `CLAUDE_*` env vars in the container. Effective model
  list is local-only.
- **S6.4**: `config/service-registry.yaml` — litellm-gateway entry
  updated: purpose now "Local-only LLM routing"; `credentials_env`
  reduced to `[LITELLM_MASTER_KEY]`; notes block added documenting the
  Phase 13.5 deprecation. YAML re-validates clean.
- **S6.5**: CLAUDE.md "Known Hardening Trade-offs" — added
  "Cloud LLM routes deprecated platform-side (Phase 13.5)" entry
  explaining the deletion and the `claude-pro` escape hatch for human
  operators.

### §7 — Regression + smoke + close

H1 regression probe (a-h) ran with PASS=14 FAIL=0 WARN=4. All four
warnings are pre-existing per the H1 closure record (openhands.internal
DNS cache, homepage.internal 502, restic CLI, gate-specific deps for
"unspecified") — no new regressions.

Smoke test (`local-stack/smoke-test-2026-04-28.md`): all three subagent
models reachable through `:11434/v1/messages` Anthropic-compatible
endpoint with single-digit-second wall-clock for trivial prompts.
litellm-gateway `/v1/models` returns only local Ollama routes.

## Mid-execution credential exposure (and rotation)

A `grep` operation early in §6 surfaced the contents of
`~/vault-init-keys.txt` (looking for the root token) into the
conversation transcript. Per the H1 doctrine codified in the canonical
pattern README ("rotate on any unintended exposure, even if
conversation-local"), the token was rotated immediately:

- Old token sha256-12: `fe9f5d7e167d` — REVOKED
- New token sha256-12: `98535bf40db1` — operational
- `~/vault-init-keys.txt` updated; line count preserved (1);
  file-token hash matches new-token hash
- `.bak` and the `/tmp/.nrt` holder securely overwritten and unlinked
  (`rm -P`)
- Audit log captured `sys/generate-root/attempt`, three
  `sys/generate-root/update` events (last with `complete=true`), and
  `auth/token/revoke`

Procedural lesson: file-content reads of credential-bearing
**well-known paths** (`~/vault-init-keys.txt`, `~/.vault-token`,
`~/.vault-approle/<svc>/{role-id,secret-id}`,
`~/.vault-agent-secrets/<svc>/credentials.env`) require the same
hash-only / count-first discipline as unknown files. Codified as a
sub-pattern under the existing INVESTIGATION ANTI-PATTERN section in
`config/vault-agent-canonical-pattern/README.md`.

The original `INVESTIGATION ANTI-PATTERN` covered *unknown* file
contents — files whose credential-bearing nature is being investigated.
The 2026-04-28 incident showed that the rule must extend to *known*
credential-bearing files at well-known paths: just because we know what
the file contains doesn't mean we may surface it. The sub-pattern
enumerates the known paths and gives concrete WRONG/RIGHT examples
(env-injection, hash-only verification, never `cat`/`head`/`grep` without
`-c`).

## Files modified or created (single commit)

```
~/.zshrc                                                               (appended)
~/.claude/settings.json                                                (modified)
~/.claude/agents/decomposer.md                                         (created)
~/.claude/agents/implementer.md                                        (created)
~/.claude/agents/reviewer.md                                           (created)
control-center-stack/stacks/gateways/litellm_config.yaml               (modified)
control-center-stack/stacks/gateways/vault-agent-litellm/credentials.env.tmpl  (modified)
config/vault-policies/litellm-gateway-policy.hcl                       (modified)
config/service-registry.yaml                                           (modified)
config/vault-agent-canonical-pattern/README.md                         (modified)
CLAUDE.md                                                              (modified)
docs/phase-13/local-stack/baseline.md                                  (created prior)
docs/phase-13/local-stack/smoke-test-2026-04-28.md                     (created)
docs/phase-13/PHASE_13_5_LOCAL_ORCHESTRATION_RESULTS_2026-04-28.md     (created — this file)
```

(The shell rc, the user-scoped `~/.claude/` files, and the out-of-repo
`~/control-center-stack/` files are not tracked by the
integrated-ai-platform git repo. The single commit captures the
in-repo subset: CLAUDE.md, config/service-registry.yaml,
config/vault-policies/litellm-gateway-policy.hcl,
config/vault-agent-canonical-pattern/README.md, and the two
docs/phase-13/local-stack/ files plus this closing report. The
out-of-repo edits are noted in the commit body.)

## Operational state at close

- Vault: sealed=false, audit log capturing, new ephemeral root token
  in `~/vault-init-keys.txt`
- 42 containers up, 0 restarting
- litellm-gateway: healthy, local-only model surface
- Open-WebUI: healthy, upstream is litellm-gateway (local-only)
- Subagent chain: all three models respond through
  Anthropic-compatible endpoint
- `claude-local` and `claude-pro` shell functions live in
  `~/.zshrc`; alias `claude=claude-local` makes local the default

## Carryover

Items deferred from prior phases remain deferred (no change):

- DEDICATED SESSION (4): T2.2 8 bin/ scripts refactoring,
  ZABBIX_ADMIN_PASSWORD rotation, T3.2 sandbox image,
  ANTHROPIC_API_KEY populate (now obsolete — Anthropic dependency
  removed; this carryover item is RESOLVED by deletion)
- DEFERRED (3): D.1 git history scrub, D.2 obot/plane superuser
  separation, D.3 plane-migrate init container coupling

Phase 13.5 itself has no carryover.
