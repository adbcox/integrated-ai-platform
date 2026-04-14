# Stage-5 Dual-Literal Boundary Pack

This pack exercises the Stage-5 manager with four scenarios:

1. **dual_success.json** – two fixture edits succeed and produce a Stage-5 commit.
2. **stale_anchor.json** – one entry references an anchor that no longer exists (Stage-4 reports `literal_replace_missing_old`).
3. **over_budget.json** – uses the same fixtures but forces `--max-total-lines 2`, triggering the Stage-5 batch budget guard.
4. **unsafe_target.json** – attempts to edit `bin/stage4_manager.py`, which Stage-4 refuses to touch.

Run `bin/micro_lane_stage5.sh` from a clean tree to replay the probes. The script
resets to the starting HEAD after each scenario so the repository stays clean.
