# Stage 3 Micro-Lane Regression Pack

This folder contains message templates that exercise the currently supported fast micro-lane class.
Run `bin/micro_lane_regression.sh` from a clean working tree to replay:

1. Accepted literal wording probe (`literal_ok.msg`).
2. Accepted comment-only probe (`comment_ok.msg`).
3. Literal-miss rejection (`literal_miss.msg`).
4. Shell-control rejection (`shell_risky.msg`).
5. Guard/aider-exit recovery (`guard_banner.msg`).

The regression script automatically reverts any accepted edits so the repository remains clean.
