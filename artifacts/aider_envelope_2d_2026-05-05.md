# Aider envelope benchmark (2D matrix)

- Date: 2026-05-05
- Sample size: 36 runs

## Per-task success rate

| task type | tier hint | success rate | cliff |
|---|---|---:|---|
| `docstring-add` | Tier 1 | 22% | 5234 (1/1 cumulative success) |
| `bare-except-narrow` | Tier 1 | 0% | 5234 (1/1 cumulative success) |
| `type-hint-add` | Tier 2 | 0% | 5234 (1/1 cumulative success) |
| `function-extract` | Tier 2 | 0% | 5234 (1/1 cumulative success) |

## Per-file success rate across tasks

| file | success rate | best/worst note |
|---|---:|---|
| `bin/aider_lib.py` | 0% | no successes |
| `bin/aider_worker.py` | 25% | docstring-add |
| `bin/aider_benchmark.py` | 25% | docstring-add |
| `bin/stage5_manager.py` | 0% | no successes |
| `bin/aider_guard.py` | 0% | no successes |
| `bin/level10_qualify.py` | 0% | no successes |
| `framework/worker_runtime.py` | 0% | no successes |
| `domains/coding.py` | 0% | no successes |
| `bin/codex51_learning_loop.py` | 0% | no successes |

## File-size cliff by task type

| task type | cliff | success rate |
|---|---|---:|
| `docstring-add` | 5234 (1/1 cumulative success) | 0% |
| `bare-except-narrow` | 5234 (1/1 cumulative success) | 0% |
| `type-hint-add` | 5234 (1/1 cumulative success) | 0% |
| `function-extract` | 5234 (1/1 cumulative success) | 0% |

## Routing recommendation

- `docstring-add`: Tier 1 for small, structurally narrow files; route Tier 2 once the file is large enough to trigger repeated escalation or timeout behavior in the sample
- `bare-except-narrow`: Tier 1 after the insertion-expansion threshold tune; keep structural context in the prompt and avoid pure line-number disambiguation
- `type-hint-add`: Tier 2
- `function-extract`: Tier 2

Note: the raw benchmark matrix was captured before the insertion-expansion threshold was widened from 3x to 8x. The bare-except regression pass after that tune is the relevant indicator for that task shape.

## Results

| task | file | size bytes | lines | defs/classes | prompt tokens | seconds | exit | diff bytes | L1 | L1.5 | success |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| `docstring-add` | `bin/aider_lib.py` | 5234 | 150 | 15 | 1327 | 35.06 | 0 | 930 | 1 | AGREE | 0 |
| `docstring-add` | `bin/aider_worker.py` | 7999 | 238 | 13 | 1958 | 48.63 | 0 | 2140 | 1 | AGREE | 1 |
| `docstring-add` | `bin/aider_benchmark.py` | 15639 | 411 | 20 | 3928 | 119.51 | 0 | 0 | 1 | N-A | 1 |
| `docstring-add` | `bin/stage5_manager.py` | 22844 | 587 | 22 | 5729 | 211.42 | 0 | 0 | 1 | N-A | 0 |
| `docstring-add` | `bin/aider_guard.py` | 24434 | 653 | 22 | 6117 | 218.59 | 0 | 0 | 1 | N-A | 0 |
| `docstring-add` | `bin/level10_qualify.py` | 25626 | 644 | 19 | 6425 | 0.09 | 1 | 0 | 1 | N-A | 0 |
| `docstring-add` | `framework/worker_runtime.py` | 42165 | 1004 | 28 | 10559 | 0.09 | 1 | 0 | 1 | N-A | 0 |
| `docstring-add` | `domains/coding.py` | 29735 | 808 | 19 | 7439 | 0.09 | 1 | 0 | 1 | N-A | 0 |
| `docstring-add` | `bin/codex51_learning_loop.py` | 114713 | 2695 | 59 | 28696 | 0.08 | 1 | 0 | 1 | N-A | 0 |
| `bare-except-narrow` | `bin/aider_lib.py` | 5234 | 150 | 15 | 1324 | 0.09 | 1 | 0 | 1 | N-A | 0 |
| `bare-except-narrow` | `bin/aider_worker.py` | 7999 | 238 | 13 | 1956 | 0.09 | 1 | 0 | 1 | N-A | 0 |
| `bare-except-narrow` | `bin/aider_benchmark.py` | 15639 | 411 | 20 | 3925 | 0.08 | 1 | 0 | 1 | N-A | 0 |
| `bare-except-narrow` | `bin/stage5_manager.py` | 22844 | 587 | 22 | 5726 | 0.08 | 1 | 0 | 1 | N-A | 0 |
| `bare-except-narrow` | `bin/aider_guard.py` | 24434 | 653 | 22 | 6114 | 0.08 | 1 | 0 | 1 | N-A | 0 |
| `bare-except-narrow` | `bin/level10_qualify.py` | 25626 | 644 | 19 | 6422 | 0.08 | 1 | 0 | 1 | N-A | 0 |
| `bare-except-narrow` | `framework/worker_runtime.py` | 42165 | 1004 | 28 | 10557 | 0.08 | 1 | 0 | 1 | N-A | 0 |
| `bare-except-narrow` | `domains/coding.py` | 29735 | 808 | 19 | 7436 | 0.08 | 1 | 0 | 1 | N-A | 0 |
| `bare-except-narrow` | `bin/codex51_learning_loop.py` | 114713 | 2695 | 59 | 28694 | 0.09 | 1 | 0 | 1 | N-A | 0 |
| `type-hint-add` | `bin/aider_lib.py` | 5234 | 150 | 15 | 1323 | 0.09 | 1 | 0 | 1 | N-A | 0 |
| `type-hint-add` | `bin/aider_worker.py` | 7999 | 238 | 13 | 1954 | 0.08 | 1 | 0 | 1 | N-A | 0 |
| `type-hint-add` | `bin/aider_benchmark.py` | 15639 | 411 | 20 | 3924 | 0.08 | 1 | 0 | 1 | N-A | 0 |
| `type-hint-add` | `bin/stage5_manager.py` | 22844 | 587 | 22 | 5725 | 0.08 | 1 | 0 | 1 | N-A | 0 |
| `type-hint-add` | `bin/aider_guard.py` | 24434 | 653 | 22 | 6113 | 0.09 | 1 | 0 | 1 | N-A | 0 |
| `type-hint-add` | `bin/level10_qualify.py` | 25626 | 644 | 19 | 6421 | 0.08 | 1 | 0 | 1 | N-A | 0 |
| `type-hint-add` | `framework/worker_runtime.py` | 42165 | 1004 | 28 | 10555 | 0.09 | 1 | 0 | 1 | N-A | 0 |
| `type-hint-add` | `domains/coding.py` | 29735 | 808 | 19 | 7435 | 0.09 | 1 | 0 | 1 | N-A | 0 |
| `type-hint-add` | `bin/codex51_learning_loop.py` | 114713 | 2695 | 59 | 28692 | 0.08 | 1 | 0 | 1 | N-A | 0 |
| `function-extract` | `bin/aider_lib.py` | 5234 | 150 | 15 | 1336 | 0.08 | 1 | 0 | 1 | N-A | 0 |
| `function-extract` | `bin/aider_worker.py` | 7999 | 238 | 13 | 1967 | 0.08 | 1 | 0 | 1 | N-A | 0 |
| `function-extract` | `bin/aider_benchmark.py` | 15639 | 411 | 20 | 3937 | 0.08 | 1 | 0 | 1 | N-A | 0 |
| `function-extract` | `bin/stage5_manager.py` | 22844 | 587 | 22 | 5738 | 0.08 | 1 | 0 | 1 | N-A | 0 |
| `function-extract` | `bin/aider_guard.py` | 24434 | 653 | 22 | 6126 | 0.08 | 1 | 0 | 1 | N-A | 0 |
| `function-extract` | `bin/level10_qualify.py` | 25626 | 644 | 19 | 6434 | 0.09 | 1 | 0 | 1 | N-A | 0 |
| `function-extract` | `framework/worker_runtime.py` | 42165 | 1004 | 28 | 10568 | 0.09 | 1 | 0 | 1 | N-A | 0 |
| `function-extract` | `domains/coding.py` | 29735 | 808 | 19 | 7448 | 0.08 | 1 | 0 | 1 | N-A | 0 |
| `function-extract` | `bin/codex51_learning_loop.py` | 114713 | 2695 | 59 | 28705 | 0.09 | 1 | 0 | 1 | N-A | 0 |
