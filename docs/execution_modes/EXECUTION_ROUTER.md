# Execution Router

## Purpose

This document tells operators and coding assistants which execution mode to use for which class of work.

Use it to minimize prompt drift, reduce document search cost, and ensure that different tools are used for the work they are best suited for.

## General routing rules

1. Prefer the **local path first** when it can complete the task within current capability limits.
2. Use **control-window modes** for truth, closure, and contradiction review.
3. Use **execution modes** for bounded implementation work.
4. Use **tool-specific mode docs** instead of ad hoc prompting whenever possible.
5. If a task spans planning + execution, separate the framework/decomposition phase from the tactical execution phase.

## Primary routing table

| Task type | Default mode | Fallback mode | Notes |
|---|---|---|---|
| Roadmap truth audit / closeout review | `CODEX_CONTROL_MODE.md` | `LOCAL_CONTROL_WINDOW_MODE.md` | Use strict truth-first review |
| Bounded documentation/governance normalization | `CODEX_EXEC_MODE.md` | `LOCAL_AIDER_EXEC_MODE.md` | Prefer Codex for broad structured doc rewrites |
| Bounded local code patch | `LOCAL_AIDER_EXEC_MODE.md` | `CODEX_EXEC_MODE.md` | Aider first for tactical validator-driven code work |
| Framework/decomposition for complex local task | `LOCAL_CONTROL_WINDOW_MODE.md` | `CODEX_CONTROL_MODE.md` | Produce bounded packet first |
| Multi-file bounded implementation | `LOCAL_AIDER_EXEC_MODE.md` | `CODEX_EXEC_MODE.md` | Escalate only if local path proves insufficient |
| Apple/Xcode/macOS implementation | `CLAUDE_CODE_EXEC_MODE.md` | `CODEX_EXEC_MODE.md` | Use where Apple toolchain access matters |
| Repo-wide contradiction / drift review | `CODEX_CONTROL_MODE.md` | `LOCAL_CONTROL_WINDOW_MODE.md` | Read-heavy, write-light by default |
| Connector/workflow implementation | `LOCAL_AIDER_EXEC_MODE.md` | `CODEX_EXEC_MODE.md` | Use local first unless tool access/environment argues otherwise |
| Local runtime / model runbook work | `LOCAL_AIDER_EXEC_MODE.md` | `CODEX_EXEC_MODE.md` | Keep changes bounded and validator-backed |

## Escalation rules

### Local Aider → Codex execution
Escalate when:
- local bounded attempts fail repeatedly on the same blocker
- the change requires broader structured rewriting than the local path is handling well
- the local model cannot form or execute a valid bounded packet

### Local / Codex → Claude Code
Escalate when:
- the task is Apple/Xcode/macOS-specific
- environment/tool access makes Claude Code materially more suitable
- the task is blocked on capabilities not present in the local path

### Any execution mode → control mode
Escalate to control mode when:
- completion is disputed
- truth surfaces may be inconsistent
- a closure claim must be verified
- there is evidence of drift or contradiction

## Required companion docs

Before using a mode, also read:
- `docs/governance/CURRENT_OPERATING_CONTEXT.md`
- `docs/roadmap/ROADMAP_AUTHORITY.md`
- relevant canonical item YAML
- relevant derived planning surfaces if queue/blocker/dependency state matters

## Notes

This router chooses the default **working surface**, not absolute exclusivity.
If a task requires a different tool for a bounded reason, document the reason in the execution packet or prompt packet.
