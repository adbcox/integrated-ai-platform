# Git Auto-Push Hook (post-commit)

## Purpose

Keep `origin/main` continuously aligned with local `main` by auto-running
`git push origin main` after each successful commit.

## Install

From repo root:

```bash
scripts/install-post-commit-push-hook.sh
```

This installs a local hook at `.git/hooks/post-commit`.

## Behavior

- Runs `git push origin main` in background after each commit.
- Fail-soft: commit succeeds even if push fails (offline, auth error, remote issue).
- Logs every attempt to `.git/push.log`.
- Skips auto-push when merge or interactive/non-interactive rebase is in progress.

## Audit / Troubleshooting

- Hook path: `.git/hooks/post-commit`
- Log path: `.git/push.log`

Inspect recent push attempts:

```bash
tail -50 .git/push.log
```

Re-install hook after clone, hook deletion, or local hook reset:

```bash
scripts/install-post-commit-push-hook.sh
```
