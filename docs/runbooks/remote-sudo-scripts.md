# Remote sudo scripts (ssh) — canonical pattern

## Purpose

Prevent automation failures caused by non-interactive `ssh` + `sudo`
execution posture on remote hosts.

Cross-reference: Finding 16 in
`docs/architecture-facts/integration-audit-doctrine.md`.

## Canonical pattern

For remote privileged operations, use:

```bash
ssh -t <host> "sudo <command>"
```

For multi-line remote blocks:

```bash
ssh -t <host> "sudo /bin/bash -s" <<'REMOTE_EOF'
set -euo pipefail
# privileged commands here
REMOTE_EOF
```

## When to use `ssh -t`

- Script executes privileged commands remotely (`sudo install`,
  `launchctl bootstrap system`, writes under `/Library`, etc.).
- Host sudo policy expects a tty-backed interactive context.
- Deliverable needs unattended reproducibility from operator shell.

## When manual sequence is canonical

Use manual sequence when:

- Remote host policy still blocks scripted sudo even with `ssh -t`.
- The operation is rare and safety-critical enough that explicit
  operator confirmation per step is preferred.

If manual path is used, script/runbook must output:

1. exact `scp` copy command,
2. exact remote `sudo` commands in order,
3. verification command(s),
4. expected success signal.

## Askpass helper stance

Do not introduce ad-hoc askpass helpers as default. They add local
secret-handling complexity and are not required for the current
headless-server doctrine. Prefer `ssh -t` first, then explicit manual
sequence if needed.

## Worked examples

- D-17-58: Mac Studio Ollama LaunchDaemon install initially failed
  under non-interactive remote sudo; operator completed manual sudo
  sequence.
- D-17-59: install script updated to `ssh -t` pattern.
