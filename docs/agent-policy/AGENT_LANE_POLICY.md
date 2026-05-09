# Agent Lane Policy

**Source:** Local AI Workstation Roadmap §9–§15 (feat/foundation-install-track-2)
**Date:** 2026-05-10
**Purpose:** Define the role and non-role of each agent tool in the local AI workstation.

---

## 9. OpenCode executor lane

### Role

OpenCode is the primary terminal coding executor candidate. It should replace Aider only for task classes where benchmark artifacts show it performs better or equally with fewer interventions and no safety regression.

**Use OpenCode for:**

```
terminal-driven coding tasks
iterative code refinement
multi-file changes
repository-aware edits
small-to-medium task scale
```

### Non-role

```
Do not use OpenCode as the silent production code editor.
Do not run OpenCode without worktree isolation.
Do not use OpenCode without permission profile enforcement.
```

### Permission profile

`eval_edit` — edit isolated worktree, run tests with approval.

### Default model

**Canonical:** `qwen3-coder:30b-coding` (Mac Studio Thunderbolt)
**MacBook substitute (E-003):** `qwen2.5-coder` via LiteLLM proxy `http://localhost:4000`

---

## 10. Goose control-plane lane

### Role

Goose is the broad workstation and control-plane agent.

**Use Goose for:**

```
research synthesis
benchmark artifact summaries
task routing
coding-agent task briefs
Zabbix incident summaries
QNAP runbook summaries
Home Assistant/digital twin summaries
ARR/media health summaries
Plane ticket drafts
RSS intelligence triage
configuration review
```

### Non-role

```
Do not use Goose as the silent production code editor.
```

### Permission profile

`read_only` — read files, summarize, no writes (with optional `ops_write_draft` for Plane drafts).

### Default model

**Canonical:** `qwen3-coder:30b-coding` (Mac Studio Thunderbolt)
**MacBook substitute (E-003):** `qwen2.5-coder` via LiteLLM proxy `http://localhost:4000`

---

## 11. Serena MCP code-intelligence layer

### Role

Serena is the semantic code-intelligence layer. It should be treated as mandatory for serious multi-file code tasks.

**Use Serena for:**

```
symbol search
definition lookup
reference lookup
repo structure analysis
semantic navigation
safe refactor planning
large-codebase context reduction
```

### Non-role — Delay or gate

```
semantic edits
automated refactors
write tools
cross-repo operations
```

### Permission profile

`read_only` — read-only code intelligence, no edits.

### Default model

Not applicable (Serena is a code-intelligence MCP, not a generative model client).

---

## 12. Aider baseline lane

### Role

Aider remains the frozen baseline and fallback executor.

**Use Aider for:**

```
small Git-native patches
known baseline comparisons
fallback when OpenCode fails twice
architect/editor experiments
controlled diff/commit behavior
```

### Non-role

```
Do not use Aider as the permanent system center.
```

### Permission profile

`eval_edit` — edit isolated worktree, run tests with approval.

### Default model

**Canonical:** `ollama_chat/qwen3-coder:30b-coding` (direct Ollama model name)
**MacBook substitute (E-003):** Use LiteLLM model_name `qwen2.5-coder` when configuring via proxy.

---

## 13. Cline IDE lane

### Role

Cline is the IDE-supervised autonomous lane.

**Use Cline for:**

```
front-end bugs
browser testing
VS Code-supervised tasks
visual diff review
workspace Problems panel fixes
interactive Plan/Act work
```

### Non-role

```
Do not use Cline as the terminal core.
```

### Permission profile

`eval_edit` — edit isolated worktree, run tests with approval (IDE-supervised).

### Default model

**Canonical:** `qwen3-coder:30b-coding` (Mac Studio Thunderbolt)
**MacBook substitute (E-003):** `qwen2.5-coder` via LiteLLM proxy `http://localhost:4000`

---

## 14. Continue helper lane

### Role

Continue is an IDE helper, not an autonomous executor.

**Use Continue for:**

```
autocomplete
codebase Q&A
lightweight local chat
review/checks
developer convenience
```

### Non-role

```
Do not use Continue as an autonomous task executor.
```

### Permission profile

`read_only` — read-only IDE helper, no autonomous edits.

### Default model

**Canonical:** `qwen3-coder:30b-coding` (Mac Studio Thunderbolt)
**MacBook substitute (E-003):** `qwen2.5-coder` via LiteLLM proxy `http://localhost:4000`

---

## 15. OpenHands sandbox lane

### Role

OpenHands is a sandbox-only full-project autonomy experiment.

**Use OpenHands only for:**

```
copied repos
containerized experiments
SWE-bench-like tasks
no secrets
no production mounts
artifact export only
```

### Non-role

```
Do not use OpenHands with production repos.
Do not mount secrets into OpenHands containers.
Do not use OpenHands for live editing of canonical repos.
Do not export artifacts without human review.
```

### Permission profile

`sandbox_autonomy` — isolated container, copied repo, no secrets.

### Default model

**Canonical:** `qwen3-coder:30b-coding` (Mac Studio Thunderbolt)
**MacBook substitute (E-003):** `qwen2.5-coder` via LiteLLM proxy `http://localhost:4000`

---

## Host-specific substitution note (E-003)

On MacBook (roaming workstation without Thunderbolt Bridge to Mac Studio):

| Canonical element | MacBook substitute |
|---|---|
| Thunderbolt Bridge endpoint `10.55.0.1:11434` | LiteLLM proxy `http://localhost:4000` |
| Model name `qwen3-coder:30b-coding` (raw Ollama) | LiteLLM model_name `qwen2.5-coder` |
| LAN fallback `192.168.10.142:11434` | Not available (offline mode uses local Ollama) |

This substitution applies throughout all lanes' configurations. Configs are **not** cross-host portable; apply host-specific endpoint and model substitutions when deploying to a different host.
