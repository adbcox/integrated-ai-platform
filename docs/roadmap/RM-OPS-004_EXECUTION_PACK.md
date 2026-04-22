# RM-OPS-004 — Execution Pack

## Title

**RM-OPS-004 — Backup, restore, disaster-recovery, and configuration export verification**

## Objective

Make the platform recoverable by defining and verifying backup, restore, disaster-recovery, and configuration export/import posture.

## Why this matters

A system with local data, memory, CMDB, and automation is not operationally credible without recovery capability.

## Required outcome

- backup inventory and policy
- restore procedure model
- disaster-recovery scenarios
- configuration export/import rules
- recovery verification checklist

## Required artifacts

- backup coverage matrix
- restore runbook template
- DR scenario table
- config export/import schema
- recovery verification report

## Best practices

- distinguish data backup from configuration backup
- test restores, not just backups
- preserve versioning and environment context in exports
- define RPO/RTO style expectations where useful

## Common failure modes

- backups that are never restore-tested
- missing configuration export posture
- no distinction between local cache and critical state

## Recommended first milestone

Build the backup coverage matrix and restore verification checklist first, then test at least one bounded restore path.
