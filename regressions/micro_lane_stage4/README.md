# Stage 4 Boundary Battery

This pack exercises the proposed Stage 4 lane:

1. `literal3_guard.msg` – attempts a three-line literal wording change in `bin/aider_loop.sh` (currently rejected as `aider_exit_guard`).
2. `comment2_ok.msg` – updates two adjacent comment lines in `bin/detect_changed_files.sh` (accepted).
3. `literal_miss.msg` – missing-anchor scenario representing a broader rewrite attempt.
4. `shell_risky.msg` – shell-control token replacement rejection.

Run `bin/micro_lane_stage4.sh` from a clean tree to replay outcomes; the script resets to HEAD after each probe.
