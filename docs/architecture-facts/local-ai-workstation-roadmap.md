# Local Open-Source AI Workstation Architecture and Implementation Roadmap

**Document status:** Corrected implementation plan
**Prepared for:** Adrian Cox
**Date:** 2026-05-06
**Primary use:** Hand off to Claude Code / Codex / local agents for implementation
**Baseline source:** `local_claude_code_replacement_architecture_master_v3(1).md`

---

## 0. Executive correction

The prior architecture correctly moved away from an Aider-centered system, but it still reads too much like a catalog of agent tools. The corrected architecture is a **local open-source AI workstation system** with a governed control plane.

The system is not:

```text
Aider plus helpers
OpenCode plus helpers
a pile of coding agents
a local-only chatbot
an IDE extension stack
```

The system is:

```text
A local-first AI operating layer for coding, research, operations, automation,
incident triage, task preparation, infrastructure review, artifact production,
and progressive replacement of cloud coding agents through evidence gates.
```

The core design principle:

```text
The center of the system is not an agent.
The center is the control plane:
  - artifact schema
  - worktree isolation
  - permission profiles
  - model routing
  - MCP tool registry
  - promotion gates
  - benchmark evidence
  - rollback discipline
```

OpenCode is the primary terminal coding executor candidate. Goose is the broad workstation/control-plane agent. Serena MCP is the semantic code-intelligence layer. Aider remains the frozen baseline and fallback. Cline and Continue are IDE lanes. OpenHands is sandbox-only. Ollama on the Mac Studio is the shared local model host. The Mac Mini is the orchestration/operator layer. QNAP stores artifacts, logs, runbooks, benchmarks, and failure corpora.

---

## 1. Hardware and network topology

### 1.1 Physical hosts

| Host | Hardware | RAM | Role | Address / connection |
|---|---:|---:|---|---|
| **Mac Studio** | M3 Ultra | 96 GB unified | Primary model execution host | `192.168.10.142` plus Thunderbolt Bridge |
| **Mac Mini** | M4 Pro | 48 GB unified | Orchestration, operator, terminal/IDE agent host | `192.168.10.145` plus Thunderbolt Bridge |
| **Threadripper + RTX 4070 12 GB** | CUDA workstation | system RAM + 12 GB VRAM | CUDA experiment lane | Secondary only |
| **QNAP NAS** | NAS | n/a | Durable artifact, log, runbook, backup, and failure-corpus store | Local network mount |

### 1.2 Role correction: “main executioner”

Use this terminology precisely:

```text
Mac Studio = model execution host / inference server
Mac Mini   = orchestration host / operator workstation / agent client host
```

The Mac Studio should execute model inference through Ollama. It should not become the place where all agents edit repos, run IDEs, or accumulate operational state. The Mac Mini should run OpenCode, Goose, Aider, Cline, Continue, dashboards, terminals, worktrees, wrappers, artifact emitters, and review tools.

### 1.3 Thunderbolt connection policy

Because the Mac Mini and Mac Studio are connected over Thunderbolt ports, treat Thunderbolt Bridge as the preferred low-latency host-to-host path for model traffic if stable.

Recommended policy:

```text
Primary inference path:
  Mac Mini agent clients -> Thunderbolt Bridge -> Mac Studio Ollama

Fallback inference path:
  Mac Mini agent clients -> LAN Ethernet/Wi-Fi -> Mac Studio Ollama
```

Implementation requirements:

1. Configure **Thunderbolt Bridge** on both Macs.
2. Assign static private IPs on the Thunderbolt Bridge interface.
3. Keep the existing LAN IPs for ordinary management.
4. Bind Ollama only to trusted interfaces or restrict by firewall.
5. Test both native Ollama API and OpenAI-compatible API over Thunderbolt Bridge.
6. Record latency and throughput in the system health log.

Suggested Thunderbolt Bridge addressing:

```text
Mac Studio Thunderbolt Bridge: 10.55.0.1/30
Mac Mini Thunderbolt Bridge:   10.55.0.2/30
```

If this is configured, the preferred Ollama endpoint becomes:

```text
Native Ollama:
  http://10.55.0.1:11434

OpenAI-compatible:
  http://10.55.0.1:11434/v1
```

Keep LAN fallback:

```text
Native Ollama:
  http://192.168.10.142:11434

OpenAI-compatible:
  http://192.168.10.142:11434/v1
```

### 1.4 Ollama binding rule

Preferred:

```bash
export OLLAMA_HOST=10.55.0.1:11434
ollama serve
```

If binding to the Thunderbolt Bridge IP is unreliable:

```bash
export OLLAMA_HOST=0.0.0.0:11434
ollama serve
```

If using `0.0.0.0`, restrict access using the macOS firewall, router rules, or a local packet filter so only the Mac Mini and trusted hosts can reach port `11434`.

### 1.5 Health checks from Mac Mini

Run from the Mac Mini:

```bash
curl -fsS http://10.55.0.1:11434/api/tags
curl -fsS http://10.55.0.1:11434/v1/models

curl -fsS http://192.168.10.142:11434/api/tags
curl -fsS http://192.168.10.142:11434/v1/models
```

Interpretation:

```text
/api/tags   = native Ollama API
/v1/models  = OpenAI-compatible API
```

Both should work because different tools use different endpoint styles.

---

## 2. Corrected system architecture

### 2.1 Target architecture

```text
                         ┌──────────────────────────────┐
                         │          Human Owner          │
                         │ approval / review / steering  │
                         └───────────────┬──────────────┘
                                         │
                                         ▼
┌──────────────────────────────────────────────────────────────────┐
│             Local AI Workstation Control Plane                   │
│                                                                  │
│ Goose recipes | task router | MCP registry | artifact logger     │
│ permission profiles | Plane drafts | Zabbix summaries            │
│ prompt library | worktree manager | verifier integration         │
└───────────────┬────────────────────────┬─────────────────────────┘
                │                        │
                ▼                        ▼
       ┌─────────────────┐       ┌─────────────────────┐
       │ Coding lanes    │       │ Workstation lanes    │
       │                 │       │                     │
       │ OpenCode        │       │ research intake      │
       │ Aider           │       │ RSS/briefings        │
       │ Cline           │       │ Zabbix triage        │
       │ Continue        │       │ QNAP runbooks        │
       │ OpenHands       │       │ Home Assistant       │
       └────────┬────────┘       │ ARR/media ops        │
                │                │ Plane ticket drafts   │
                │                └──────────┬──────────┘
                │                           │
                ▼                           ▼
       ┌──────────────────────────────────────────────┐
       │ Serena MCP and other read-mostly MCP tools   │
       │ semantic code navigation / references        │
       └──────────────────┬───────────────────────────┘
                          │
                          ▼
       ┌──────────────────────────────────────────────┐
       │ Mac Studio Ollama model server               │
       │ Thunderbolt endpoint preferred               │
       └──────────────────┬───────────────────────────┘
                          │
                          ▼
       ┌──────────────────────────────────────────────┐
       │ QNAP durable artifact and memory layer       │
       │ JSONL / markdown logs / runbooks / failures  │
       └──────────────────────────────────────────────┘
```

### 2.2 Correct division of labor

| Component | Correct role | Incorrect role |
|---|---|---|
| **Goose** | Workstation control-plane agent, router, summarizer, recipe runner, non-code automation | Unrestricted production executor |
| **OpenCode** | Primary Claude Code-style terminal coding executor candidate | Whole-system center |
| **Serena MCP** | Shared semantic code-intelligence layer | Optional novelty |
| **Aider** | Frozen Git-native baseline and fallback | Permanent destination |
| **Cline** | IDE-supervised Plan/Act lane | Terminal core |
| **Continue** | IDE helper/autocomplete/checks | Autonomous executor |
| **OpenHands** | Sandboxed autonomy experiment | Daily production agent |
| **Ollama** | Shared local inference host | General workflow orchestrator |
| **QNAP** | Artifact, evidence, memory, backup layer | Agent scratchpad with broad write access |

---

## 3. Recommended versions and version policy

### 3.1 Version policy

Because these tools are moving quickly, the correct policy is:

```text
Use latest stable release at the time of installation.
Record exact versions into the artifact log.
Pin versions for each benchmark cycle.
Do not compare agent performance across unrecorded version drift.
```

Every implementation run must create:

```text
agent_environment/versions-YYYY-MM-DD.md
```

### 3.2 Known current versions as of 2026-05-06

These are reference versions observed during this plan preparation. Verify before installation.

| Tool | Reference current version | Recommended use |
|---|---:|---|
| **OpenCode** | `v1.14.40` observed as latest GitHub release | Install latest stable; pin for benchmark cycle |
| **Goose** | `v1.33.1` observed as latest GitHub release | Install latest stable; avoid release candidates initially |
| **Serena** | `v1.2.0` observed as latest GitHub release | Install latest stable |
| **OpenHands** | `1.7.0` observed as latest GitHub release | Sandbox only |
| **Aider** | Use latest stable from official installer/PyPI | Pin exact output of `aider --version` |
| **Ollama** | Use latest stable macOS build | Pin exact output of `ollama --version` |
| **Continue** | Use current stable VS Code extension | Record extension version |
| **Cline** | Use current stable VS Code extension | Record extension version |

### 3.3 Required version capture commands

Run on Mac Mini:

```bash
mkdir -p ~/local-ai-workstation/agent_environment

{
  echo "# Local AI Workstation Versions"
  echo
  echo "Date: $(date -Iseconds)"
  echo
  echo "## Host"
  hostname
  sw_vers
  uname -a
  echo
  echo "## Tools"
  command -v opencode && opencode --version || true
  command -v goose && goose --version || true
  command -v aider && aider --version || true
  command -v serena && serena --version || true
  command -v ollama && ollama --version || true
  command -v node && node --version || true
  command -v npm && npm --version || true
  command -v python3 && python3 --version || true
  command -v uv && uv --version || true
  command -v git && git --version || true
} > ~/local-ai-workstation/agent_environment/versions-$(date +%F).md
```

Run on Mac Studio:

```bash
mkdir -p ~/local-ai-workstation/agent_environment

{
  echo "# Mac Studio Model Host Versions"
  echo
  echo "Date: $(date -Iseconds)"
  echo
  sw_vers
  uname -a
  echo
  ollama --version
  echo
  curl -fsS http://127.0.0.1:11434/api/tags || true
  curl -fsS http://127.0.0.1:11434/v1/models || true
} > ~/local-ai-workstation/agent_environment/mac-studio-versions-$(date +%F).md
```

---

## 4. Model strategy

### 4.1 Default local models

Use the existing local model stack as follows:

| Model | Role | Initial status |
|---|---|---|
| `qwen3-coder:30b-coding` | Daily coding executor, normal OpenCode/Aider/Cline use | Primary |
| `qwen3-coder-next:80B` | Hard planning, architecture, recurrence-prone failures | Heavy reasoning lane |
| `deepseek-coder-v2:16b` | Faster edit/debug lane, fallback editor model | Secondary |
| `gemma2:27b` | General comparison and non-code fallback | Secondary |

### 4.2 Context window policy

Set coding-agent contexts to at least `65536` tokens where supported.

Rationale:

```text
Aider warns that Ollama's small default context can silently discard content.
OpenCode's Ollama integration recommends at least a 64k token context window.
Large codebase agents should fail explicitly rather than silently lose context.
```

### 4.3 Model assignment policy

| Use case | Recommended model |
|---|---|
| OpenCode normal task | `qwen3-coder:30b-coding` |
| OpenCode hard plan | `qwen3-coder-next:80B` |
| Aider normal code mode | `qwen3-coder:30b-coding` |
| Aider architect model | `qwen3-coder-next:80B` |
| Aider editor model | `deepseek-coder-v2:16b` or `qwen3-coder:30b-coding` |
| Goose research/ops | `qwen3-coder:30b-coding` initially; test `gemma2:27b` for summarization |
| Continue autocomplete | fastest acceptable local model |
| Cline Plan mode | `qwen3-coder-next:80B` for hard tasks; otherwise `qwen3-coder:30b-coding` |
| OpenHands sandbox | same models but with strict artifact logging |

### 4.4 Promotion metrics for models

Do not promote a model for speed alone. Promotion requires improvement or parity across:

```text
success rate
test pass rate
recurrence_rate
multi_file_orchestration
malformed_edit_count
wall-clock task completion
operator interventions
rollback reliability
artifact completeness
```

---

## 5. Directory structure

Create this on the Mac Mini:

```bash
mkdir -p ~/local-ai-workstation/{agent_environment,agent_runs,agent_tasks,agent_briefs,agent_failures,agent_promotions,configs,docs,logs,prompts,scripts,worktrees}
```

Recommended tree:

```text
~/local-ai-workstation/
  agent_environment/
    versions-YYYY-MM-DD.md
  agent_runs/
    YYYY-MM-DD/
      opencode-<task-id>.jsonl
      aider-<task-id>.jsonl
      goose-<task-id>.jsonl
  agent_tasks/
    TASK-0001.json
  agent_briefs/
    BRIEF-0001.json
  agent_failures/
    FAILURE-0001.md
  agent_promotions/
    PROMOTION-0001.md
  configs/
    opencode/
    goose/
    aider/
    cline/
    continue/
    serena/
    openhands/
  docs/
    LOCAL_AI_WORKSTATION_ARCHITECTURE.md
    AGENT_LANE_POLICY.md
    PROMOTION_GATES.md
  logs/
  prompts/
  scripts/
  worktrees/
    opencode/
    aider/
    cline/
    openhands/
```

Mount QNAP artifacts at a stable path, for example:

```text
/Volumes/QNAP_AI/agent-artifacts/
```

Then mirror or rsync local artifacts to QNAP:

```bash
rsync -av --delete ~/local-ai-workstation/agent_runs/ /Volumes/QNAP_AI/agent-artifacts/agent_runs/
rsync -av --delete ~/local-ai-workstation/agent_failures/ /Volumes/QNAP_AI/agent-artifacts/agent_failures/
rsync -av --delete ~/local-ai-workstation/agent_promotions/ /Volumes/QNAP_AI/agent-artifacts/agent_promotions/
```

---

## 6. Worktree policy

### 6.1 Non-negotiable rule

```text
No two agents may edit the same worktree.
No agent may edit the canonical repo directly.
```

### 6.2 Worktree setup script

Create:

```text
~/local-ai-workstation/scripts/create-agent-worktrees.sh
```

Content:

```bash
#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 /path/to/repo"
  exit 1
fi

REPO="$1"
BASE="$HOME/local-ai-workstation/worktrees"
NAME="$(basename "$REPO")"

mkdir -p "$BASE"

cd "$REPO"

git status --short

git worktree add "$BASE/${NAME}-opencode" -b "agent-eval/opencode" || true
git worktree add "$BASE/${NAME}-aider" -b "agent-eval/aider" || true
git worktree add "$BASE/${NAME}-cline" -b "agent-eval/cline" || true
git worktree add "$BASE/${NAME}-openhands" -b "agent-eval/openhands" || true

echo "Created or verified agent worktrees under: $BASE"
git worktree list
```

Make executable:

```bash
chmod +x ~/local-ai-workstation/scripts/create-agent-worktrees.sh
```

### 6.3 Worktree assignment table

| Worktree | Tool | Purpose |
|---|---|---|
| canonical repo | human only | final reviewed state |
| `*-opencode` | OpenCode | terminal coding candidate |
| `*-aider` | Aider | baseline comparison |
| `*-cline` | Cline | IDE-supervised tasks |
| `*-openhands` | OpenHands | sandbox/autonomy tests |

---

## 7. Artifact schema

Create:

```text
~/local-ai-workstation/configs/AGENT_ARTIFACT_SCHEMA.json
```

Content:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Local AI Workstation Agent Run",
  "type": "object",
  "required": [
    "timestamp",
    "task_id",
    "agent",
    "host",
    "model_host",
    "provider",
    "model",
    "repo",
    "worktree",
    "task_class",
    "mode",
    "permissions_profile",
    "verifier_status"
  ],
  "properties": {
    "timestamp": { "type": "string" },
    "task_id": { "type": "string" },
    "agent": {
      "type": "string",
      "enum": ["goose", "opencode", "aider", "cline", "continue", "openhands", "human"]
    },
    "agent_version": { "type": "string" },
    "host": { "type": "string" },
    "model_host": { "type": "string" },
    "provider": { "type": "string" },
    "model": { "type": "string" },
    "endpoint": { "type": "string" },
    "repo": { "type": "string" },
    "worktree": { "type": "string" },
    "branch": { "type": "string" },
    "task_class": {
      "type": "string",
      "enum": [
        "simple_edit",
        "bugfix",
        "stack_trace_bug",
        "multi_file_orchestration",
        "refactor",
        "docker_service_setup",
        "mcp_scaffolding",
        "frontend_visual_bug",
        "ops",
        "research",
        "incident",
        "media",
        "home_automation",
        "plane_ticket",
        "runbook"
      ]
    },
    "prompt_hash": { "type": "string" },
    "prompt_path": { "type": "string" },
    "mode": { "type": "string" },
    "permissions_profile": { "type": "string" },
    "context_sources": { "type": "array", "items": { "type": "string" } },
    "files_read": { "type": "array", "items": { "type": "string" } },
    "files_modified": { "type": "array", "items": { "type": "string" } },
    "commands_run": { "type": "array", "items": { "type": "string" } },
    "tests_run": { "type": "array", "items": { "type": "string" } },
    "mcp_tools_used": { "type": "array", "items": { "type": "string" } },
    "external_apis_called": { "type": "array", "items": { "type": "string" } },
    "diff_lines_added": { "type": "integer" },
    "diff_lines_removed": { "type": "integer" },
    "wall_clock_seconds": { "type": "number" },
    "time_to_first_token": { "type": ["number", "null"] },
    "tokens_per_second": { "type": ["number", "null"] },
    "malformed_edit_count": { "type": "integer" },
    "loop_detected": { "type": "boolean" },
    "doom_loop_triggered": { "type": "boolean" },
    "operator_interventions": { "type": "integer" },
    "rollback_available": { "type": "boolean" },
    "rollback_success": { "type": ["boolean", "null"] },
    "verifier_status": {
      "type": "string",
      "enum": ["pass", "fail", "partial", "not_run"]
    },
    "failure_class": { "type": ["string", "null"] },
    "recurrence_rate_impact": {
      "type": "string",
      "enum": ["improved", "worsened", "neutral", "unknown"]
    },
    "multi_file_orchestration_result": {
      "type": "string",
      "enum": ["pass", "fail", "not_applicable"]
    },
    "notes": { "type": "string" }
  }
}
```

---

## 8. Permission profiles

### 8.1 Global permission doctrine

```text
Default posture: read-mostly.
Escalate writes only by lane.
Never allow secrets access by default.
Never allow remote push by default.
Never allow sudo by default.
Never allow destructive filesystem or Docker commands by default.
```

### 8.2 Profiles

| Profile | Intended tool | Permission level |
|---|---|---|
| `read_only` | Goose, Serena, Continue | read files, summarize, no writes |
| `plan_only` | OpenCode, Cline, Aider architect planning | inspect, propose, no edits |
| `eval_edit` | OpenCode/Aider/Cline worktrees | edit isolated worktree, run tests with approval |
| `ops_read` | Goose ops workflows | read logs/runbooks/status exports |
| `ops_write_draft` | Goose Plane drafts | create drafts only, no live production changes |
| `sandbox_autonomy` | OpenHands | isolated container, copied repo, no secrets |
| `human_approved_production` | human-triggered only | reviewed merge or deployment actions |

### 8.3 Destructive commands requiring approval

```text
rm
mv over existing path
git reset --hard
git clean
docker compose down -v
docker volume rm
docker system prune
sudo
chmod -R
chown -R
secret rotation
database migrations
remote push
Vault access
QNAP bulk delete
```

---

## 9. OpenCode executor lane

### 9.1 Role

OpenCode is the primary terminal coding executor candidate. It should replace Aider only for task classes where benchmark artifacts show it performs better or equally with fewer interventions and no safety regression.

### 9.2 Installation

Preferred official install:

```bash
curl -fsSL https://opencode.ai/install | bash
```

Homebrew option if available and preferred:

```bash
brew install anomalyco/tap/opencode
```

Verify:

```bash
opencode --version
```

### 9.3 Different ways to start OpenCode

#### Direct project start

```bash
cd ~/local-ai-workstation/worktrees/<repo>-opencode
opencode
```

Inside OpenCode:

```text
/init
/models
/permissions
```

#### Ollama launch method

```bash
ollama launch opencode
```

Configuration-only launch:

```bash
ollama launch opencode --config
```

#### Explicit environment endpoint

```bash
export OLLAMA_HOST=http://10.55.0.1:11434
cd ~/local-ai-workstation/worktrees/<repo>-opencode
opencode
```

### 9.4 `opencode.json`

Create:

```text
~/local-ai-workstation/configs/opencode/opencode.json
```

Recommended content:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "ollama": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Ollama on Mac Studio Thunderbolt",
      "options": {
        "baseURL": "http://10.55.0.1:11434/v1"
      },
      "models": {
        "qwen3-coder:30b-coding": {
          "name": "Qwen3 Coder 30B Coding"
        },
        "qwen3-coder-next:80B": {
          "name": "Qwen3 Coder Next 80B"
        },
        "deepseek-coder-v2:16b": {
          "name": "DeepSeek Coder V2 16B"
        },
        "gemma2:27b": {
          "name": "Gemma2 27B"
        }
      }
    },
    "ollama_lan_fallback": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Ollama on Mac Studio LAN fallback",
      "options": {
        "baseURL": "http://192.168.10.142:11434/v1"
      },
      "models": {
        "qwen3-coder:30b-coding": {
          "name": "Qwen3 Coder 30B Coding"
        },
        "qwen3-coder-next:80B": {
          "name": "Qwen3 Coder Next 80B"
        },
        "deepseek-coder-v2:16b": {
          "name": "DeepSeek Coder V2 16B"
        },
        "gemma2:27b": {
          "name": "Gemma2 27B"
        }
      }
    }
  },
  "model": "ollama/qwen3-coder:30b-coding",
  "permission": {
    "*": "ask",
    "read": {
      "*": "allow",
      "*.env": "deny",
      "*.env.*": "deny",
      "*.pem": "deny",
      "*.key": "deny",
      "*.p12": "deny",
      "*.mobileprovision": "deny",
      "*.env.example": "allow"
    },
    "grep": "allow",
    "glob": "allow",
    "edit": "ask",
    "bash": {
      "*": "ask",
      "pwd": "allow",  # pragma: allowlist secret
      "ls *": "allow",
      "find *": "allow",
      "rg *": "allow",
      "grep *": "allow",
      "git status*": "allow",
      "git diff*": "allow",
      "git log*": "allow",
      "git branch*": "allow",
      "git worktree list*": "allow",
      "python -m pytest*": "ask",
      "pytest*": "ask",
      "npm test*": "ask",
      "npm run test*": "ask",
      "npm run lint*": "ask",
      "ruff check*": "ask",
      "mypy*": "ask",
      "git commit*": "ask",
      "git push*": "deny",
      "rm *": "deny",
      "sudo *": "deny",
      "chmod -R*": "deny",
      "chown -R*": "deny",
      "docker compose down*": "ask",
      "docker compose up*": "ask",
      "docker system prune*": "deny"
    },
    "external_directory": "ask",
    "doom_loop": "ask",
    "webfetch": "ask",
    "websearch": "ask",
    "task": "ask"
  }
}
```

Copy or symlink this into project worktrees:

```bash
cp ~/local-ai-workstation/configs/opencode/opencode.json ~/local-ai-workstation/worktrees/<repo>-opencode/opencode.json
```

### 9.5 AGENTS.md starter

Create in each OpenCode worktree after `/init`, then edit to:

```markdown
# AGENTS.md

## Mission

Operate as a local, evidence-producing coding agent. Make small, reversible, testable changes. Do not optimize for appearing autonomous; optimize for verified improvement.

## Operating modes

Use Plan mode before Build mode for:

- multi-file changes
- refactors
- Docker or service configuration
- MCP server scaffolding
- recurrence-prone benchmark cases
- config/security/deployment changes

Build mode may be used directly only for low-risk one-file tasks.

## Safety rules

- Do not read `.env`, private keys, certificates, or secret files.
- Do not run `sudo`.
- Do not push to remotes.
- Do not delete files without approval.
- Do not run destructive Docker commands without approval.
- Do not edit outside this worktree without approval.
- Do not modify canonical production repos.

## Verification

After edits, run the verification commands listed in `VERIFICATION.md` or the task brief.

If verification cannot be run, explain exactly why.

## Artifact requirement

At the end of every task, produce a summary with:

- task id
- files read
- files changed
- commands run
- tests run
- result
- known risks
- rollback instructions
- recommended JSONL artifact fields
```

### 9.6 OpenCode special words and commands

Use consistently:

```text
/init              initialize project agent instructions
/models            select or inspect model
/permissions       inspect/change permission behavior
Plan mode          inspect and propose
Build mode         implement after plan
```

Operational phrases to use in prompts:

```text
"Plan only. Do not edit files yet."
"Inspect the repository first."
"Use Serena for symbol lookup before editing."
"Make the smallest reversible change."
"Run the verifier before summarizing."
"Emit an artifact summary."
"Stop if you need access to secrets."
"Do not touch files outside this worktree."
```

---

## 10. Goose control-plane lane

### 10.1 Role

Goose is the broad workstation and control-plane agent.

Use Goose for:

```text
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

Do not use Goose as the silent production code editor.

### 10.2 Installation

Install latest stable Goose CLI/Desktop from official source.

Verify:

```bash
goose --version
goose configure
```

### 10.3 Goose provider configuration

Run:

```bash
goose configure
```

Select:

```text
Configure Providers
Ollama
Model: qwen3-coder:30b-coding
API Host: http://10.55.0.1:11434
```

Fallback:

```text
API Host: http://192.168.10.142:11434
```

### 10.4 Goose profiles

Create distinct local-only profiles:

```text
goose-local-control-plane
goose-local-coding-briefs
goose-local-research
goose-local-ops
goose-local-media
goose-local-zabbix
goose-local-plane
goose-local-home-assistant
```

Policy:

```text
No cloud-provider profile should be used for local-first benchmarks.
Cloud profiles, if kept, must be named explicitly and never used by default.
```

### 10.5 Goose recipes to create

Create recipe files under:

```text
~/local-ai-workstation/configs/goose/recipes/
```

Initial recipes:

```text
001-summarize-benchmark-artifacts.yaml
002-create-opencode-task-brief.yaml
003-zabbix-incident-summary.yaml
004-arr-health-report.yaml
005-research-log-to-plane-ticket.yaml
006-qnap-runbook-review.yaml
007-home-assistant-digital-twin-summary.yaml
008-agent-promotion-review.yaml
```

### 10.6 Goose task brief template

```json
{
  "task_id": "TASK-0000",
  "task_summary": "",
  "preferred_executor": "opencode",
  "repo": "",
  "worktree": "",
  "files_likely_relevant": [],
  "evidence": [],
  "commands_to_run_first": [],
  "constraints": [],
  "risk_level": "low",
  "definition_of_done": "",
  "handoff_reason": "",
  "serena_required": true,
  "artifact_required": true,
  "rollback_expectation": ""
}
```

### 10.7 Goose routing policy

| Input | Goose action |
|---|---|
| Research topic | Write research-log entry |
| Incident/log bundle | Summarize and classify |
| User asks for code change | Create task brief, route to OpenCode/Aider/Cline |
| Benchmark results | Produce promotion review |
| Plane ticket request | Draft ticket, do not auto-create until approved |
| Home Assistant/Zabbix/QNAP review | Read-only summary first |
| ARR/media maintenance | Read-only health report first |

---

## 11. Serena MCP code-intelligence layer

### 11.1 Role

Serena is the semantic code-intelligence layer. It should be treated as mandatory for serious multi-file code tasks.

Use Serena for:

```text
symbol search
definition lookup
reference lookup
repo structure analysis
semantic navigation
safe refactor planning
large-codebase context reduction
```

Delay or gate:

```text
semantic edits
automated refactors
write tools
cross-repo operations
```

### 11.2 Installation

Install Serena using its recommended current installer. If using `uv`:

```bash
uv tool install serena
```

Verify:

```bash
serena --version
```

If the shell cannot find `serena`, use the full executable path in MCP client configuration.

### 11.3 MCP configuration principle

Use per-workspace Serena configuration for coding clients where possible.

Correct pattern:

```text
Start Serena with:
  --project /path/to/current/worktree
```

Avoid a global Serena server that silently switches between projects unless the client requires it.

### 11.4 Serena benchmark policy

Every multi-file benchmark must test:

```text
OpenCode without Serena
OpenCode with Serena
Aider without Serena
Aider with Serena if practical
Cline with Serena if practical
```

A coding-agent result is incomplete unless it records whether Serena was used.

---

## 12. Aider baseline lane

### 12.1 Role

Aider remains the frozen baseline and fallback executor.

Use Aider for:

```text
small Git-native patches
known baseline comparisons
fallback when OpenCode fails twice
architect/editor experiments
controlled diff/commit behavior
```

Do not use Aider as the permanent system center.

### 12.2 Installation

Recommended:

```bash
python3 -m pip install --upgrade aider-chat
```

or use `uv`:

```bash
uv tool install aider-chat
```

Verify:

```bash
aider --version
```

### 12.3 Aider Ollama configuration

Aider should use `ollama_chat/` for local Ollama models.

Create in repo root or worktree:

```text
.aider.conf.yml
```

Recommended baseline:

```yaml
model: ollama_chat/qwen3-coder:30b-coding
map-tokens: 4096
cache-prompts: true
auto-commits: true
dirty-commits: false
show-diffs: true
read:
  - CONVENTIONS.md
  - DEBUGGING.md
  - VERIFICATION.md
```

Create:

```text
.aider.model.settings.yml
```

Recommended baseline:

```yaml
- name: ollama_chat/qwen3-coder:30b-coding
  edit_format: diff
  extra_params:
    num_ctx: 65536
    temperature: 0

- name: ollama_chat/deepseek-coder-v2:16b
  edit_format: diff
  extra_params:
    num_ctx: 32768
    temperature: 0

- name: ollama_chat/qwen3-coder-next:80B
  edit_format: diff
  extra_params:
    num_ctx: 65536
    temperature: 0
```

### 12.4 Starting Aider

#### Normal code mode

```bash
cd ~/local-ai-workstation/worktrees/<repo>-aider
aider --model ollama_chat/qwen3-coder:30b-coding
```

#### Ask-only mode

```bash
aider --chat-mode ask --model ollama_chat/qwen3-coder:30b-coding
```

Use for:

```text
repo Q&A
planning
code explanation
no file edits
```

#### Architect mode at launch

```bash
aider \
  --architect \
  --model ollama_chat/qwen3-coder-next:80B \
  --editor-model ollama_chat/qwen3-coder:30b-coding
```

#### Architect mode from inside Aider

Inside Aider:

```text
/architect
```

or:

```text
/chat-mode architect
```

Use Architect mode when:

```text
multi-file planning is needed
model has edit-format trouble
complex refactor needs separation between reasoning and editing
you need a planning model plus a focused editor model
```

### 12.5 Aider special words and commands

```text
/add          add files to chat context
/drop         remove files from chat context
/ask          ask without editing
/code         return to code-editing mode
/architect    enter architect/editor mode
/run          run shell command
/test         run configured test command
/commit       commit current changes
/diff         show current diff
```

Prompt phrases:

```text
"Use architect mode."
"First propose the architecture; do not edit until the plan is clear."
"Use the editor model only for precise file changes."
"Keep the patch small and reversible."
"Commit only after tests pass."
```

---

## 13. Cline IDE lane

### 13.1 Role

Cline is the IDE-supervised autonomous lane.

Use for:

```text
front-end bugs
browser testing
VS Code-supervised tasks
visual diff review
workspace Problems panel fixes
interactive Plan/Act work
```

Do not use Cline as the terminal core.

### 13.2 Configuration

Configure against Mac Studio Ollama through OpenAI-compatible or Ollama provider support:

```text
Base URL:
  http://10.55.0.1:11434/v1

Fallback:
  http://192.168.10.142:11434/v1

Model:
  qwen3-coder:30b-coding
```

### 13.3 Operational rule

Use Cline’s Plan/Act split:

```text
Plan first.
Act only after approval.
No unattended destructive commands.
Use the Cline worktree only.
```

---

## 14. Continue helper lane

### 14.1 Role

Continue is an IDE helper, not an autonomous executor.

Use for:

```text
autocomplete
codebase Q&A
lightweight local chat
review/checks
developer convenience
```

### 14.2 Configuration

Example local Ollama configuration:

```json
{
  "models": [
    {
      "title": "Mac Studio Qwen3 Coder Thunderbolt",
      "provider": "ollama",
      "model": "qwen3-coder:30b-coding",
      "apiBase": "http://10.55.0.1:11434"
    },
    {
      "title": "Mac Studio Qwen3 Coder LAN fallback",
      "provider": "ollama",
      "model": "qwen3-coder:30b-coding",
      "apiBase": "http://192.168.10.142:11434"
    }
  ]
}
```

---

## 15. OpenHands sandbox lane

### 15.1 Role

OpenHands is a sandbox-only full-project autonomy experiment.

Use only for:

```text
copied repos
containerized experiments
SWE-bench-like tasks
no secrets
no production mounts
artifact export only
```

### 15.2 Hard restrictions

```text
No canonical repo edits.
No direct QNAP write access except artifact export directory.
No Vault access.
No .env access.
No host Docker destructive control.
No production service credentials.
No persistent unattended autonomy.
```

---

## 16. Zabbix checks

Add Zabbix items for:

```text
Mac Studio Ollama native API reachable over Thunderbolt
Mac Studio Ollama OpenAI-compatible API reachable over Thunderbolt
Mac Studio Ollama native API reachable over LAN fallback
Mac Studio Ollama OpenAI-compatible API reachable over LAN fallback
Mac Mini can reach Mac Studio
OpenCode binary available
Goose binary available
Aider binary available
Serena binary available
QNAP artifact path mounted
QNAP artifact path writable
agent worktrees clean
Mac Studio memory pressure
Mac Mini memory pressure
Ollama model list includes qwen3-coder:30b-coding
Ollama model list includes qwen3-coder-next:80B
Ollama model list includes deepseek-coder-v2:16b
```

Example local check commands:

```bash
curl -fsS http://10.55.0.1:11434/api/tags >/dev/null
curl -fsS http://10.55.0.1:11434/v1/models >/dev/null
curl -fsS http://192.168.10.142:11434/api/tags >/dev/null
curl -fsS http://192.168.10.142:11434/v1/models >/dev/null
command -v opencode >/dev/null
command -v goose >/dev/null
command -v aider >/dev/null
command -v serena >/dev/null
test -w /Volumes/QNAP_AI/agent-artifacts
```

---

## 17. Work breakdown structure

### 17.1 WBS overview

```text
1.0 Governance and architecture
2.0 Host/network setup
3.0 Artifact and directory setup
4.0 Model host setup
5.0 Agent client installation
6.0 Tool configuration
7.0 Worktree isolation
8.0 Benchmark and verifier integration
9.0 Workstation workflows
10.0 Zabbix monitoring
11.0 Promotion gates
12.0 Documentation and handoff
```

### 17.2 Detailed WBS

| WBS | Work package | Owner | Output | Acceptance criteria |
|---:|---|---|---|---|
| 1.1 | Rename architecture to Local AI Workstation | Claude/Codex | Markdown docs | Clear scope beyond coding |
| 1.2 | Define lane policy | Claude/Codex | `AGENT_LANE_POLICY.md` | Each tool has role and non-role |
| 1.3 | Define permission profiles | Claude/Codex | `AGENT_PERMISSION_PROFILES.md` | Read/write/destructive rules explicit |
| 2.1 | Configure Thunderbolt Bridge | Human/Codex | static IPs | Mac Mini reaches Mac Studio on `10.55.0.1` |
| 2.2 | Configure LAN fallback | Human/Codex | fallback endpoints | LAN endpoints pass health checks |
| 2.3 | Firewall Ollama | Human/Codex | restricted port 11434 | Only trusted hosts can reach |
| 3.1 | Create local directory tree | Codex | folders | Tree exists |
| 3.2 | Mount QNAP artifact path | Human/Codex | mounted path | writable from Mac Mini |
| 3.3 | Add rsync mirror scripts | Codex | scripts | local artifacts copy to QNAP |
| 4.1 | Install/update Ollama on Mac Studio | Human/Codex | Ollama service | `/api/tags` passes |
| 4.2 | Pull required models | Human/Codex | models present | model list contains required names |
| 4.3 | Record versions | Codex | version docs | version file exists |
| 5.1 | Install OpenCode | Human/Codex | CLI | `opencode --version` |
| 5.2 | Install Goose | Human/Codex | CLI/Desktop | `goose --version` |
| 5.3 | Install Aider | Human/Codex | CLI | `aider --version` |
| 5.4 | Install Serena | Human/Codex | CLI/MCP | `serena --version` |
| 5.5 | Install Cline | Human | VS Code extension | extension visible |
| 5.6 | Install Continue | Human | VS Code extension | extension visible |
| 5.7 | Install OpenHands | Human/Codex | sandbox only | sandbox launches |
| 6.1 | Configure OpenCode | Codex | `opencode.json` | connects to Thunderbolt Ollama |
| 6.2 | Configure Goose profiles | Codex | config/profiles | local profile works |
| 6.3 | Configure Aider | Codex | `.aider.*` files | normal and architect modes launch |
| 6.4 | Configure Serena MCP | Codex | MCP config | symbol lookup works |
| 6.5 | Configure Continue | Human/Codex | extension config | local model responds |
| 6.6 | Configure Cline | Human/Codex | extension config | local model responds |
| 7.1 | Create worktree script | Codex | shell script | creates four worktrees |
| 7.2 | Enforce worktree policy | Human/Codex | doc + checks | no agent edits canonical repo |
| 8.1 | Create JSONL schema | Codex | schema file | validates sample artifact |
| 8.2 | Create wrapper templates | Codex | scripts | run emits artifact stub |
| 8.3 | Define benchmark matrix | Claude/Codex | benchmark doc | 8 task classes listed |
| 8.4 | Define verifier gates | Claude/Codex | gates doc | recurrence/multi-file metrics included |
| 9.1 | Create Goose recipes | Codex | YAML recipes | first 8 recipes exist |
| 9.2 | Create task brief template | Codex | JSON template | OpenCode handoff complete |
| 9.3 | Create Plane draft template | Codex | Markdown/JSON | no auto-write by default |
| 10.1 | Add Zabbix checks | Human/Codex | checks | all checks visible |
| 10.2 | Add dashboards | Human/Codex | dashboard | model/artifact health visible |
| 11.1 | Run OpenCode vs Aider A/B | Human/Codex | JSONL runs | same task, both tools |
| 11.2 | Run OpenCode with/without Serena | Human/Codex | JSONL runs | Serena impact measurable |
| 11.3 | Review promotion | Goose/Human | promotion memo | lane decision recorded |
| 12.1 | Create handoff package | Claude/Codex | docs/scripts/configs | implementable by Claude Code |
| 12.2 | Freeze v1 baseline | Human | tag/archive | baseline reproducible |

---

## 18. Implementation schedule

### Phase 0 — Architecture freeze

**Duration:** 0.5 day
**Goal:** Stop architecture drift.

Tasks:

```text
0.1 Rename document set to Local AI Workstation.
0.2 Freeze lane policy.
0.3 Freeze hardware roles.
0.4 Freeze promotion metrics.
0.5 Create implementation repository/folder.
```

Deliverables:

```text
LOCAL_AI_WORKSTATION_ARCHITECTURE.md
AGENT_LANE_POLICY.md
PROMOTION_GATES.md
```

Exit criteria:

```text
The system is described as lanes plus control plane, not tool collection.
```

---

### Phase 1 — Network and model host foundation

**Duration:** 1 day
**Goal:** Make Mac Studio a reliable model execution host reachable from Mac Mini over Thunderbolt and LAN fallback.

Tasks:

```text
1.1 Configure Thunderbolt Bridge static IPs.
1.2 Confirm Mac Mini -> Mac Studio ping over Thunderbolt.
1.3 Bind Ollama to Thunderbolt Bridge or trusted interfaces.
1.4 Confirm /api/tags and /v1/models over Thunderbolt.
1.5 Confirm LAN fallback.
1.6 Pull/verify required models.
1.7 Record host versions.
1.8 Add firewall restrictions.
```

Exit criteria:

```text
Mac Mini can reliably reach Mac Studio Ollama over Thunderbolt and LAN fallback.
Both native and OpenAI-compatible endpoints work.
```

---

### Phase 2 — Artifact/control-plane foundation

**Duration:** 1 day
**Goal:** Create the evidence system before running agents.

Tasks:

```text
2.1 Create ~/local-ai-workstation tree.
2.2 Mount or configure QNAP artifact store.
2.3 Create JSONL schema.
2.4 Create sample artifact.
2.5 Create artifact validation script.
2.6 Create rsync mirror script.
2.7 Create version capture script.
2.8 Create task brief template.
```

Exit criteria:

```text
Every agent run has a place to write evidence.
Artifacts can be mirrored to QNAP.
```

---

### Phase 3 — Install and configure primary lanes

**Duration:** 1-2 days
**Goal:** Bring up Goose, OpenCode, Serena, and Aider first.

Tasks:

```text
3.1 Install OpenCode.
3.2 Configure OpenCode with Thunderbolt Ollama endpoint.
3.3 Install Goose.
3.4 Configure Goose local-only provider/profile.
3.5 Install Serena.
3.6 Configure Serena MCP for one test repo.
3.7 Install/verify Aider.
3.8 Configure Aider normal and architect modes.
3.9 Record exact versions.
```

Exit criteria:

```text
OpenCode, Goose, Serena, and Aider can all reach local models.
No cloud model is required.
```

---

### Phase 4 — Worktree and safety enforcement

**Duration:** 0.5-1 day
**Goal:** Prevent tool collision and production contamination.

Tasks:

```text
4.1 Create worktree setup script.
4.2 Create agent worktrees for first target repo.
4.3 Add AGENTS.md to OpenCode worktree.
4.4 Add .aider config to Aider worktree.
4.5 Add permission profile docs.
4.6 Verify no tool uses canonical repo.
4.7 Verify no two agents share a worktree.
```

Exit criteria:

```text
Each agent has a dedicated worktree.
Canonical repo remains untouched.
```

---

### Phase 5 — First benchmark cycle

**Duration:** 2 days
**Goal:** Compare OpenCode, Aider, and Serena impact.

Tasks:

```text
5.1 Select simple one-file bug task.
5.2 Run Aider baseline.
5.3 Run OpenCode baseline.
5.4 Select multi-file orchestration task.
5.5 Run OpenCode without Serena.
5.6 Run OpenCode with Serena.
5.7 Run Aider baseline.
5.8 Emit JSONL artifacts for each.
5.9 Use Goose to summarize results.
5.10 Write promotion memo.
```

Exit criteria:

```text
At least one task class has evidence comparing OpenCode vs Aider.
At least one task class has evidence comparing Serena vs no Serena.
```

---

### Phase 6 — IDE lanes

**Duration:** 1 day
**Goal:** Add Cline and Continue after core lanes are stable.

Tasks:

```text
6.1 Install Continue.
6.2 Configure Continue to Thunderbolt Ollama.
6.3 Install Cline.
6.4 Configure Cline to Thunderbolt Ollama / OpenAI-compatible endpoint.
6.5 Assign Cline worktree.
6.6 Run one front-end/browser/IDE task.
6.7 Record artifact manually if needed.
```

Exit criteria:

```text
IDE lanes work but do not compete with terminal/control-plane lanes.
```

---

### Phase 7 — Workstation workflows

**Duration:** 2-3 days
**Goal:** Prove the system is not coding-only.

Tasks:

```text
7.1 Create Goose benchmark summary recipe.
7.2 Create Goose Zabbix incident summary recipe.
7.3 Create Goose QNAP runbook review recipe.
7.4 Create Goose research-log-to-Plane draft recipe.
7.5 Create Goose ARR/media health recipe.
7.6 Create Goose Home Assistant summary recipe.
7.7 Run each in read-only mode.
7.8 Record artifacts.
```

Exit criteria:

```text
Goose can handle non-code workstation work in read-mostly mode.
```

---

### Phase 8 — OpenHands sandbox

**Duration:** 1 day
**Goal:** Evaluate full-project autonomy without production exposure.

Tasks:

```text
8.1 Install OpenHands sandbox.
8.2 Create copied repo fixture.
8.3 Deny secrets and production mounts.
8.4 Run one benchmark-like task.
8.5 Export artifact only.
8.6 Compare with OpenCode/Aider.
```

Exit criteria:

```text
OpenHands is either useful as sandbox experiment or deferred.
No production exposure occurs.
```

---

### Phase 9 — Monitoring and operations hardening

**Duration:** 1 day
**Goal:** Make the stack observable.

Tasks:

```text
9.1 Add Zabbix Ollama checks.
9.2 Add agent binary checks.
9.3 Add QNAP writable check.
9.4 Add model availability checks.
9.5 Add worktree cleanliness check.
9.6 Add memory pressure checks.
9.7 Build dashboard.
```

Exit criteria:

```text
Failure of model host, artifact path, or agent binary is visible.
```

---

### Phase 10 — Baseline freeze and next-cycle plan

**Duration:** 0.5 day
**Goal:** Freeze what works and plan next benchmark cycle.

Tasks:

```text
10.1 Review artifacts.
10.2 Decide whether OpenCode replaces Aider for any task class.
10.3 Decide whether Serena is mandatory for any task class.
10.4 Decide whether any model should be promoted/demoted.
10.5 Archive configs and versions.
10.6 Write next-cycle plan.
```

Exit criteria:

```text
The system has a reproducible v1 baseline.
Future changes are measured against it.
```

---

## 19. Promotion gates

### 19.1 Tool promotion

A tool may be promoted for a task class only if it satisfies:

```text
success_rate >= current baseline
test_pass_rate >= current baseline
operator_interventions <= current baseline
malformed_edit_count <= current baseline
rollback_success is not worse
recurrence_rate is improved or neutral
multi_file_orchestration is improved or neutral
artifact completeness is pass
```

### 19.2 Tool demotion

Demote or restrict a tool if:

```text
it edits wrong files
it needs repeated operator rescue
it loops
it ignores permission boundaries
it fails to summarize evidence
it increases recurrence_rate
it worsens rollback reliability
```

### 19.3 Model promotion

A model is promoted only after:

```text
same task
same tool
same worktree state
same prompt/task brief
same verifier
different model
```

Do not compare models across uncontrolled task differences.

---

## 20. Recommended prompts

### 20.1 Claude/Codex implementation prompt

```text
SYSTEM: Claude Code or Codex

Implement the Local Open-Source AI Workstation Architecture from this document.

Primary goal:
Create a governed local AI workstation stack, not a loose collection of coding agents.

Hardware:
- Mac Mini M4 Pro 48GB = orchestration/operator host
- Mac Studio M3 Ultra 96GB = Ollama model execution host
- Mac Mini and Mac Studio are connected over Thunderbolt Bridge
- QNAP = durable artifact and memory layer

Implement in this order:
1. Directory structure
2. Version capture scripts
3. Artifact schema
4. Worktree setup script
5. OpenCode config
6. Aider config
7. Goose recipe skeletons
8. Serena MCP config notes
9. Permission profile docs
10. Promotion gates
11. First benchmark plan

Constraints:
- Local-first and open-source foundation only.
- No canonical repo edits by agents.
- No two agents in the same worktree.
- No unrestricted shell access.
- No secret file access.
- No remote push.
- No sudo.
- No destructive Docker commands without approval.
- Every run must produce JSONL or an equivalent artifact summary.
- Use Thunderbolt Ollama endpoint first: http://10.55.0.1:11434
- Keep LAN fallback: http://192.168.10.142:11434
```

### 20.2 OpenCode first task prompt

```text
Plan only. Do not edit files yet.

You are running in the OpenCode executor lane of the Local AI Workstation system.

Task:
Inspect this repository and create a minimal implementation plan for the requested change.

Rules:
- Do not read .env, private key, certificate, or secret files.
- Do not edit files yet.
- Use Serena for symbol lookup if configured.
- Identify likely files.
- Identify verification commands.
- Identify rollback path.
- Identify risks.
- Produce an artifact-ready summary.
```

### 20.3 Aider architect prompt

```text
Use architect mode.

First reason about the design and produce a small, reversible implementation plan.
Then allow the editor model to make only the necessary file edits.

Rules:
- Do not touch secrets.
- Keep edits limited to this worktree.
- Prefer minimal diffs.
- Run verification before commit.
- Summarize files changed, commands run, tests run, and rollback instructions.
```

### 20.4 Goose routing prompt

```text
You are the Goose control-plane agent.

Given this task, decide whether it should be handled by:
- Goose directly
- OpenCode
- Aider
- Cline
- Continue
- OpenHands sandbox

Return a task brief with:
- task summary
- preferred executor
- worktree
- likely files
- evidence
- commands to run first
- constraints
- risk level
- definition of done
- whether Serena is required
- artifact requirements
- handoff reason
```

---

## 21. Immediate implementation checklist

```text
[ ] Configure Thunderbolt Bridge IPs.
[ ] Verify Mac Mini can reach Mac Studio over Thunderbolt.
[ ] Confirm Ollama native and /v1 endpoints.
[ ] Create ~/local-ai-workstation tree.
[ ] Mount QNAP artifact store.
[ ] Install/update OpenCode.
[ ] Install/update Goose.
[ ] Install/update Aider.
[ ] Install/update Serena.
[ ] Record versions.
[ ] Create opencode.json.
[ ] Create .aider.conf.yml and .aider.model.settings.yml.
[ ] Create AGENTS.md template.
[ ] Create worktree setup script.
[ ] Create JSONL artifact schema.
[ ] Create Goose task brief template.
[ ] Create first Goose recipes.
[ ] Run first OpenCode vs Aider benchmark.
[ ] Run first OpenCode with/without Serena benchmark.
[ ] Write first promotion memo.
```

---

## 22. Source references

The original uploaded v3 plan already establishes the corrected direction: OpenCode as the Claude Code-style terminal candidate, Goose as broad workstation agent, Aider as baseline/fallback, Cline and Continue as IDE lanes, Serena as semantic MCP tool layer, OpenHands as sandbox lane, Ollama on Mac Studio as model server, and verifier artifacts as judge.

Additional implementation references used for this corrected plan:

- OpenCode + Ollama integration: https://docs.ollama.com/integrations/opencode
- OpenCode provider configuration: https://opencode.ai/docs/providers/
- Goose + Ollama integration: https://docs.ollama.com/integrations/goose
- Goose overview, providers, MCP, recipes: https://goose-docs.ai/
- Aider + Ollama configuration: https://aider.chat/docs/llms/ollama.html
- Aider chat modes and architect mode: https://aider.chat/docs/usage/modes.html
- Aider in-chat commands: https://aider.chat/docs/usage/commands.html
- Aider edit formats for architect/editor mode: https://aider.chat/docs/more/edit-formats.html
- Serena MCP client connection documentation: https://oraios.github.io/serena/02-usage/030_clients.html
- Serena GitHub project and release/license metadata: https://github.com/oraios/serena
- OpenHands releases: https://github.com/OpenHands/OpenHands/releases
- OpenCode releases: https://github.com/anomalyco/opencode/releases
- Goose releases: https://github.com/aaif-goose/goose/releases

---

## 23. Final doctrine

```text
The Local AI Workstation is a governed system, not an agent collection.

Goose routes, summarizes, drafts, and orchestrates.
OpenCode executes Claude Code-style terminal coding tasks.
Serena supplies semantic code intelligence.
Aider preserves the baseline and fallback path.
Cline handles supervised IDE/browser tasks.
Continue assists inside the IDE.
OpenHands explores autonomy only in sandbox.
Ollama on Mac Studio executes local models.
Mac Mini orchestrates agents and workflows.
QNAP preserves evidence and memory.
Zabbix monitors health.
Plane receives human-actionable drafts.
Promotion is decided by artifacts, not preference.
```
