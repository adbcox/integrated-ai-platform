# Prompt Packet Standard

## Purpose

This document defines the standard structure for prompts sent to coding assistants, control windows, and execution tools.

Use it to reduce prompt drift, improve reuse across tools, and ensure bounded execution and acceptance rules are consistently communicated.

## Core packet fields

Every substantial prompt packet should define, as applicable:

1. **Session type**
   - control window
   - execution window
   - local aider exec
   - local control window
   - Claude Code exec

2. **Primary objective**
   - exact bounded goal

3. **Why this work matters now**
   - blocker, leverage point, or business reason

4. **Required reads**
   - exact docs/files to read first

5. **Bounded scope**
   - what is in scope
   - what is out of scope

6. **Allowed files**
   - exact files or file families allowed for modification

7. **Forbidden files**
   - exact files or file families not to touch

8. **Validation sequence**
   - exact commands and order

9. **Truth surfaces to update**
   - canonical
   - derived
   - summary

10. **Completion rule**
   - what counts as done
   - what does not count as done

11. **Stop conditions**
   - when to stop successfully
   - when to stop due to a real blocker

12. **Output format**
   - exact final report sections required

## Minimal packet template

```text
Session type:
Primary objective:
Why this matters now:
Required reads:
Bounded scope:
Allowed files:
Forbidden files:
Validation sequence:
Truth surfaces to update:
Completion rule:
Stop conditions:
Output format:
```

## Rules

- do not omit bounded scope for implementation work
- do not omit completion rule for closeout-sensitive work
- do not omit validations when validator-backed work is expected
- do not treat narrative goals as sufficient packet structure for complex tasks

## Tool-selection note

After filling the packet, route it through:
- `docs/execution_modes/EXECUTION_ROUTER.md`
- relevant tool-specific mode doc

## Notes

This standard is intentionally generic so the same packet shape can be used with Codex, Claude Code, local Aider, or local control-window flows.
