# Claude Code PreToolUse hooks — operational runbook

**Status**: Active. Installed 2026-05-01 closing audit R-03 / D-15-05.
**Hook script**: `scripts/claude-pretooluse-hook.py` (in this repo)
**Wiring**: `~/.claude/settings.json` `hooks.PreToolUse` block
**Hook log**: `/Users/admin/.platform-logs/claude-pretooluse.log`

---

## Purpose

Pattern-matches every Bash tool call Claude Code is about to execute against three rule levels (DENY / WARN / ALLOW). Designed in response to:

- 2026-04-30 Vault cascade (Sev-2 incident): destructive operations executed inside an autonomous-execution window with no operator-side gate
- 2026-05-01 morning planning-chat near-miss: a separate Claude session generated a 6-hour autonomous-execution prompt that would have rolled back two completed Phase 14 deliverables. Caught by operator before forwarding; hooks prevent it being caught only by operator vigilance

The hook is the operator-side gate: even if a planning chat produces a destructive prompt, the execution windows hook layer blocks the worst classes of commands before any state change.

## Architecture

```
Claude Code -> wants to run Bash command
            -> PreToolUse hook fires (this script)
            -> stdin: tool-call JSON
            -> Pattern match against RULES list
            -> Severity dispatch:
                 DENY -> exit 2 + stderr reason -> Claude Code blocks
                 WARN -> exit 0 + log entry      -> Claude Code proceeds
                 no match -> exit 0 silent       -> Claude Code proceeds
            -> Append to /Users/admin/.platform-logs/claude-pretooluse.log
```

## Rule levels

### DENY (hard block)

Categories and example patterns: Vault destructive ops (operator init, operator force-leave, audit disable, volume rm against vault); Docker/Colima destructive (colima delete, compose down with volumes flag against critical-state stacks); Backup destructive (mc rm recursive against qnap/backups, restic forget without retention); Filesystem destructive (rm -rf root, repo, home, repos dir); Git destructive (push force without lease, reset hard to specific commit, filter-branch, update-ref delete).

When DENY fires, the operator sees the block reason on stderr. To intentionally proceed, the operator runs the command manually outside Claude Code.

### WARN (log only, allowed)

Volume rm (any), stop on critical services, git checkout HEAD discarding working tree, git reset hard without target, chmod 777, sudo invocations, backgrounded output suppression. All warned + logged but allowed.

### ALLOW (silent pass)

Anything not matching a rule.

## Adding new rules

Edit `scripts/claude-pretooluse-hook.py`. The RULES list is a sequence of (pattern, severity, reason) tuples evaluated top-to-bottom; first match wins. Patterns are Python regex matched case-insensitively against the full Bash command string.

After adding rules:

1. Run the script with self-test JSON inline (pipe a tool-call JSON to the script and check exit code)
2. Verify both DENY (exit 2) and ALLOW (exit 0) cases as expected
3. Commit with conventional commit message format

## Debugging

**Why was my command blocked?** The hooks stderr contains matched pattern + reason. The hook log at `/Users/admin/.platform-logs/claude-pretooluse.log` records every match with timestamp. Tail with `tail -50 <logpath>`.

**Hook seems not to be running:** Verify `~/.claude/settings.json` has the hooks.PreToolUse block pointing at the repo script path. Verify the script is executable. Run a quick self-test by piping a known-deny JSON.

**Hook is too aggressive / false positive:** Open the hook script, find the matching pattern, either tighten the regex (negative lookahead, anchors), move from DENY to WARN, or remove the rule. Always tighten before removing.

## Emergency disable

If the hook misbehaves and is blocking critical work: edit `~/.claude/settings.json` and remove the hooks block, OR rename the script with a .disabled suffix. Hook absence is fail-open — Claude Code proceeds normally, no commands gated. Log a doctrine note about the disable so it gets re-enabled.

## Recovery if hook script is lost

The script is in this repo at `scripts/claude-pretooluse-hook.py`. If lost on disk: `cd ~/repos/integrated-ai-platform && git checkout -- scripts/claude-pretooluse-hook.py && chmod +x scripts/claude-pretooluse-hook.py`.

## References

- `docs/phase-15/COMPREHENSIVE_AUDIT_2026-05-01.md` Section 13 Blocker 1 — the original recommendation
- `docs/phase-15/COMPREHENSIVE_AUDIT_VALIDATION_2026-05-01.md` Section 11.1 — the morning-chat near-miss
- `docs/phase-15/PHASE_15_RECOVERY_HANDOFF_2026-04-30.md` — cascade incident recovery doctrine
