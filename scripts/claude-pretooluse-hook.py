#!/usr/bin/env python3
"""
Claude Code PreToolUse hook for the Integrated AI Platform.

Reads tool-call JSON from stdin. For Bash tool calls, pattern-matches the
proposed command against three rule levels:
  - DENY: hard block (exit 2, stderr reason shown to user)
  - WARN: log only, command proceeds
  - ALLOW (no match): exit 0, command proceeds silently

All matches are logged to /Users/admin/.platform-logs/claude-pretooluse.log

Designed in response to the 2026-04-30 Vault cascade incident and the
2026-05-01 morning planning-chat near-miss (would have destroyed
observability stack via cargo-culted destructive prompts).

Reference: docs/runbooks/pretooluse-hooks.md
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

LOG_PATH = "/Users/admin/.platform-logs/claude-pretooluse.log"

# (pattern, severity, reason)
# Severity: "deny" or "warn"
RULES = [
    # --- Vault destructive operations ---
    (r"vault\s+operator\s+init\b",
     "deny",
     "vault operator init re-initializes the cluster and wipes all state."),
    (r"vault\s+operator\s+force-leave\b",
     "deny",
     "vault operator force-leave can corrupt cluster state."),
    (r"vault\s+audit\s+disable\b",
     "deny",
     "Disabling audit device removes the only record of Vault operations."),
    (r"docker\s+volume\s+rm\b.*vault[-_]",
     "deny",
     "Removing vault volumes destroys persistent Vault state."),

    # --- Docker / Colima destructive operations ---
    (r"colima\s+delete\b",
     "deny",
     "colima delete wipes the entire Docker VM (all containers + volumes)."),
    (r"docker\s+compose\s+down\s+(-v|--volumes)\b.*(vault|netbox|inventree|plane|grafana)",
     "deny",
     "compose down with --volumes on critical-state stacks destroys data."),

    # --- MinIO / backup destructive operations ---
    (r"mc\s+rm\s+[^|]*--recursive[^|]*qnap/backups",
     "deny",
     "Wiping qnap/backups bucket destroys all Restic snapshots."),
    (r"restic\s+forget.*--unsafe-allow-no-keep-policy",
     "deny",
     "restic forget without retention policy can wipe all snapshots."),

    # --- Filesystem / repo destructive operations ---
    (r"rm\s+-r?fr?\s+/(\s|$)",
     "deny",
     "rm -rf / wipes filesystem root."),
    (r"rm\s+-r?fr?\s+/Users/admin/repos/integrated-ai-platform(\s|/$|$)",
     "deny",
     "Removes the entire integrated-ai-platform repo."),
    (r"rm\s+-r?fr?\s+~/repos(\s|/$|$)",
     "deny",
     "Removes the entire repos directory."),
    (r"rm\s+-r?fr?\s+~/?\s*$",
     "deny",
     "rm -rf of home directory."),

    # --- Git destructive operations ---
    (r"git\s+push\s+(--force(?!-with-lease)|-f)(\s|$)",
     "deny",
     "git push --force can overwrite remote history irrecoverably (use --force-with-lease if needed)."),
    (r"git\s+reset\s+--hard\s+(HEAD~|HEAD\^|[a-f0-9]{7,})",
     "deny",
     "git reset --hard to a specific commit discards committed work between HEAD and target."),
    (r"git\s+filter-branch\b",
     "deny",
     "git filter-branch rewrites history irrecoverably across the repo."),
    (r"git\s+update-ref\s+-d\b",
     "deny",
     "git update-ref -d deletes refs."),

    # --- Sneaky output-hiding patterns ---
    (r">\s*/dev/null\s+2>&1\s*&\s*$",
     "warn",
     "Backgrounded output suppression hides errors from the operator."),
    (r"\|\s*tee\s+/dev/null",
     "warn",
     "tee /dev/null is suspicious — output is being redirected and discarded."),

    # --- Warn-only (allowed but logged) ---
    (r"docker\s+volume\s+rm\b",
     "warn",
     "docker volume rm destroys volume data; ensure intended."),
    (r"docker\s+stop\b.*\b(vault-server|grafana-obs|caddy|netbox|inventree|plane-api|vmagent|victoria)",
     "warn",
     "Stopping critical-service container; ensure intended."),
    (r"git\s+checkout\s+(HEAD\s+--|--\s+[\w/.])",
     "warn",
     "git checkout HEAD -- discards working-tree changes (typically intended; logging)."),
    (r"chmod\s+(0?777|a\+rwx)",
     "warn",
     "chmod 777 grants world write/execute."),
    (r"git\s+reset\s+--hard\b(?!\s+(HEAD~|HEAD\^|[a-f0-9]{7,}))",
     "warn",
     "git reset --hard discards uncommitted changes."),
    (r"sudo\s+",
     "warn",
     "sudo invocation; logged for audit."),
]


def log(message):
    """Append to log file, best-effort (never fail hook on log error)."""
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a") as f:
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            f.write(f"{ts} {message}\n")
    except Exception:
        pass


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception as e:
        log(f"hook-error: invalid JSON on stdin: {e}")
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})

    if tool_name != "Bash":
        sys.exit(0)

    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    for pattern, severity, reason in RULES:
        if re.search(pattern, command, re.IGNORECASE):
            cmd_short = command.replace("\n", " ")[:200]
            log(f"{severity.upper()} pattern={pattern!r} command={cmd_short!r} reason={reason!r}")
            if severity == "deny":
                print(f"BLOCKED by PreToolUse hook: {reason}", file=sys.stderr)
                print(f"Pattern matched: {pattern}", file=sys.stderr)
                print(f"Hook log: {LOG_PATH}", file=sys.stderr)
                print("If you genuinely intend this, run it manually outside Claude Code.", file=sys.stderr)
                sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
