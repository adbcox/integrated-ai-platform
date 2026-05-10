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
