#!/bin/sh
set -eu

# Priority ordering for detection (Stage-3/Stage-4 literal lanes + Stage-5 dual batches):
# 1) CLI args remain the operator-provided authority for Codex-managed runs
# 2) CHANGED_FILES env (space/newline separated) stays the literal override for scripted probes, now tagging Manager-4 Stage-5 entries, honoring the candidate lane's bin-only scope, and noting successes toward promotion readiness
# 3) git diff/ls-files fallback only seeds Stage-4/Stage-5 scans when nothing else is provided, and Stage-5 records the resulting scope in traces''
