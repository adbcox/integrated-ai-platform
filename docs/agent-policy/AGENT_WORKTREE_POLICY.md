# Agent Worktree Policy

**Source:** Local AI Workstation Roadmap §6.1–§6.3 (feat/foundation-install-track-2)
**Date:** 2026-05-10
**Purpose:** Define the non-negotiable worktree isolation rule and assignment.

---

## 6.1 Non-negotiable rule

```
No two agents may edit the same worktree.
No agent may edit the canonical repo directly.
```

**Rationale:** Worktree isolation prevents concurrent edits from different agents, ensuring that benchmarking results are not confounded by agent-to-agent interference. The canonical repo remains a single source of truth and final gate for all merged work.

---

## 6.2 Worktree setup script

The script `/agent-orchestration/scripts/create-agent-worktrees.sh` creates agent worktrees for any target repository.

**Usage:**

```bash
/Users/adriancox/repos/integrated-ai-platform/agent-orchestration/scripts/create-agent-worktrees.sh /path/to/repo
```

Or via symlink:

```bash
~/local-ai-workstation/scripts/create-agent-worktrees.sh /path/to/repo
```

**What it does:**

1. Takes a repo path as argument (typically absolute path to a cloned repository)
2. Creates worktrees under `~/local-ai-workstation/worktrees/` with the repo name as prefix
3. Creates four agent-specific worktrees: opencode, aider, cline, openhands
4. Each worktree has its own branch: `agent-eval/<tool>`
5. Idempotent — running the script twice on the same repo is safe (uses `|| true` to suppress "already exists" errors)

**Example:**

```bash
~/local-ai-workstation/scripts/create-agent-worktrees.sh /Users/adriancox/repos/integrated-ai-platform
```

Creates:

```
~/local-ai-workstation/worktrees/integrated-ai-platform-opencode
~/local-ai-workstation/worktrees/integrated-ai-platform-aider
~/local-ai-workstation/worktrees/integrated-ai-platform-cline
~/local-ai-workstation/worktrees/integrated-ai-platform-openhands
```

---

## 6.3 Worktree assignment table

| Worktree | Tool | Purpose |
|---|---|---|
| canonical repo | human only | final reviewed state; no agent edits |
| `*-opencode` | OpenCode | terminal coding candidate; primary executor lane |
| `*-aider` | Aider | baseline comparison; frozen reference implementation |
| `*-cline` | Cline | IDE-supervised tasks; VS Code-based testing |
| `*-openhands` | OpenHands | sandbox/autonomy tests; container-isolated experiments |

---

## Enforcement

**Verification checks:**

1. **On task startup:** Agent wrapper scripts (Phase 6 WBS 8.2) verify that the agent is being invoked in its assigned worktree, not the canonical repo.
2. **On git operations:** Wrapper scripts check that git commits/pushes target the agent-eval branch, not main/master.
3. **On task completion:** Audit log confirms no edits to canonical repo.

**Failure mode:** If any agent attempts to edit the canonical repo directly, the wrapper script logs a violation, halts execution, and alerts the operator.

---

## Symlink deployment

The script is stored in the repo at:

```
/Users/adriancox/repos/integrated-ai-platform/agent-orchestration/scripts/create-agent-worktrees.sh
```

At deployment time (Phase 7), symlink to the runtime location:

```bash
ln -sf /Users/adriancox/repos/integrated-ai-platform/agent-orchestration/scripts/create-agent-worktrees.sh \
  ~/local-ai-workstation/scripts/create-agent-worktrees.sh
```

This allows operator to run the script from the local-ai-workstation directory without needing the full repo path.
