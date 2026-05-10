# Agent Permission Profiles

**Source:** Local AI Workstation Roadmap §8.1–§8.3 (feat/foundation-install-track-2)
**Date:** 2026-05-10
**Purpose:** Define permission profiles and authorization rules for all agents in the local AI workstation.

---

## 8.1 Global permission doctrine

Default posture and escalation rules:

```
Default posture: read-mostly.
Escalate writes only by lane.
Never allow secrets access by default.
Never allow remote push by default.
Never allow sudo by default.
Never allow destructive filesystem or Docker commands by default.
```

---

## 8.2 Profiles

Seven permission profiles define what each agent tool may and may not do:

| Profile | Intended tool | Permission level | Use case |
|---|---|---|---|
| `read_only` | Goose, Serena, Continue | Read files, summarize, no writes | Summarization, code intelligence, IDE helper |
| `plan_only` | OpenCode, Cline, Aider architect planning | Inspect, propose, no edits | Architecture planning before implementation |
| `eval_edit` | OpenCode/Aider/Cline worktrees | Edit isolated worktree, run tests with approval | Terminal or IDE coding tasks in sandbox |
| `ops_read` | Goose ops workflows | Read logs/runbooks/status exports | Operations review and summary |
| `ops_write_draft` | Goose Plane drafts | Create drafts only, no live production changes | Ticket generation without auto-submission |
| `sandbox_autonomy` | OpenHands | Isolated container, copied repo, no secrets | Full autonomy experiments in sandbox |
| `human_approved_production` | Human-triggered only | Reviewed merge or deployment actions | Final production-gate actions only |

### Profile summary by tool

**OpenCode:** `eval_edit` (worktree-based editing)
**Goose:** `read_only` + optional `ops_write_draft`
**Serena:** `read_only` (code intelligence only)
**Aider:** `eval_edit` or `plan_only` (baseline)
**Cline:** `eval_edit` (IDE-supervised)
**Continue:** `read_only` (IDE helper)
**OpenHands:** `sandbox_autonomy` (container isolation)

---

## 8.3 Destructive commands requiring approval

The following commands MUST NOT be executed by any agent without explicit human approval. This list is enforced via wrapper scripts and runtime guards:

```
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

Each agent wrapper script must:
1. Intercept any destructive command in the agent's output
2. Log the command with context (user, task, timestamp)
3. Refuse execution and ask for human confirmation before proceeding
4. Record approval/denial in the artifact log

---

## Implementation guidance

### For OpenCode (`eval_edit`)

```
Allowed:
  cd <worktree>
  git diff, git add, git commit
  editor operations on files in the worktree
  bash for testing and validation
  git push to worktree-branch only

Denied by default:
  Any destructive commands (see §8.3)
  Remote push to canonical repo
  Secret access
  Sudo operations
  Cross-worktree edits
```

### For Goose (`read_only` and `ops_write_draft`)

```
Allowed:
  File reads (non-secret)
  Log inspection
  Config file reads
  Writing Plane draft tickets (ops_write_draft only)
  Summary and synthesis outputs

Denied by default:
  Any file writes (except Plane drafts in ops_write_draft)
  Destructive commands (see §8.3)
  Secret access
  Remote operations
  Production changes
```

### For Serena (`read_only`)

```
Allowed:
  Symbol search
  Definition lookup
  Reference lookup
  Repo structure analysis

Denied by default:
  Any write operations
  Edits to code
  Project modifications
  Model inference (Serena is code-intelligence MCP only)
```

### For Aider (`eval_edit` or `plan_only`)

```
Allowed (eval_edit):
  File edits in the worktree
  git diff, git commit
  Testing and validation

Allowed (plan_only):
  Code inspection
  Architectural proposals
  Planning output

Denied by default:
  Destructive commands (see §8.3)
  Remote push to canonical repo
  Cross-worktree edits
  Secret access
```

### For Cline (`eval_edit`)

```
Allowed:
  File edits in the worktree (IDE-supervised)
  Interactive Plan/Act workflow
  VS Code command palette integration
  Browser testing commands

Denied by default:
  Unattended destructive operations
  Cross-worktree edits
  Secret access
  Non-IDE terminal operations
```

### For Continue (`read_only`)

```
Allowed:
  Autocomplete suggestions
  Codebase Q&A (via chat)
  Local code chat
  Review/checks feedback

Denied by default:
  Autonomous file edits
  Destructive commands (see §8.3)
  Secret access
  Production operations
```

### For OpenHands (`sandbox_autonomy`)

```
Allowed:
  Full autonomy within the container
  Container-local file operations
  Package installations
  Build and test commands
  Artifact export

Denied by default:
  Host filesystem access
  Secret mounts
  Production repo editing
  Cross-container operations
```

---

## Wrapper script responsibilities

Each agent wrapper (see WBS 8.2) must:

1. **Enforce permission profile** before executing the agent
2. **Intercept destructive commands** (§8.3 list) and require approval
3. **Log all operations** with task ID, timestamp, user, and outcome
4. **Emit artifact stubs** (pre/post) in the standard schema
5. **Collect evidence** (task state, model output, exit codes)
6. **Fail safely** — if permission check fails, log and halt (do not fall through)

---

## Approval workflow

When an agent attempts a destructive or restricted command:

1. Wrapper intercepts the command
2. Wrapper logs: `[APPROVAL REQUIRED] <command> in task <task_id>`
3. Wrapper outputs the context (what, why, which file)
4. Wrapper waits for human input (approve/deny)
5. If approved: execute and log approval
6. If denied: log denial and skip the command
7. Artifact log records the decision

---

## Audit and compliance

**Every agent run must produce:**

- Pre-run artifact snapshot (task state)
- Execution log (commands attempted, permissions checked, denials logged)
- Post-run artifact snapshot (output state)
- Any approvals/denials recorded with justification

**Compliance check:** Run a weekly audit script that verifies no destructive command was executed without a corresponding approval entry in the artifact log.
