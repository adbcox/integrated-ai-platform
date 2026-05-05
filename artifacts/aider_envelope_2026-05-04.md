# Aider envelope benchmark

- Date: 2026-05-04
- Prompt: `Add type hints to all function signatures.`
- Sample size: 9 files

## Cliff summary
- Size cliff: no stable green envelope in this sample; the smallest sampled file (5234 bytes) failed, and the only clean success was at 7999 bytes.
- Function-count cliff: no stable green envelope in this sample; the only clean success was on a 13-definition file.

## Results

| file | size bytes | lines | defs/classes | prompt tokens | seconds | exit | diff bytes | L1 | L1.5 | success |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| `bin/aider_lib.py` | 5234 | 150 | 15 | 1319 | 42.22 | 4 | 1735 | 0 | N-A | 0 |
| `bin/aider_worker.py` | 7999 | 238 | 13 | 1951 | 51.51 | 0 | 1046 | 1 | AGREE | 1 |
| `bin/aider_benchmark.py` | 15639 | 411 | 20 | 3921 | 119.64 | 4 | 3483 | 0 | N-A | 0 |
| `bin/stage5_manager.py` | 22844 | 587 | 22 | 5722 | 112.76 | 0 | 0 | 0 | N-A | 0 |
| `bin/aider_guard.py` | 24434 | 653 | 22 | 6109 | 0.08 | 1 | 7402 | 0 | N-A | 0 |
| `bin/level10_qualify.py` | 25626 | 644 | 19 | 6417 | 0.08 | 1 | 0 | 0 | N-A | 0 |
| `framework/worker_runtime.py` | 42165 | 1004 | 28 | 10552 | 0.08 | 1 | 0 | 0 | N-A | 0 |
| `domains/coding.py` | 29735 | 808 | 19 | 7432 | 0.08 | 1 | 0 | 0 | N-A | 0 |
| `bin/codex51_learning_loop.py` | 114713 | 2695 | 59 | 28689 | 0.08 | 1 | 0 | 0 | N-A | 0 |
