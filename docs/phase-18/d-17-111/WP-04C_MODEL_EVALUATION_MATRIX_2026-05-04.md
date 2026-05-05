# D-17-111 WP-04C — Verifier model evaluation matrix

**Date:** 2026-05-04
**Status:** SURFACE-BACK — candidate selected, no default flip yet
**Scope:** Compare verifier model/prompt combinations on the D-17-111 wrong-target case and a clean correction case.

## Test cases

| Case | Description |
|---|---|
| Wrong-target diff | Diff changed the specific `except json.JSONDecodeError` clause instead of the bare `except:` target |
| Clean diff | Diff changed the bare `except:` target in the intended block |

## Matrix

| Verifier stack | Wrong-target verdict | Clean diff verdict | Notes |
|---|---|---|---|
| `deepseek-coder-v2:16b-lite-instruct-q4_K_M` + v1.0.0 prompt | AGREE | not remeasured here | False-negative blind spot on repeated-target diff |
| `deepseek-coder-v2:16b-lite-instruct-q4_K_M` + v1.1.0 prompt | AGREE | not remeasured here | Still false-negatives the wrong-target case |
| `qwen3-coder-next:coding` + v1.1.0 prompt | AGREE | not remeasured here | Still false-negatives the wrong-target case |
| `qwen3-coder:30b-coding` + v1.1.0 prompt | DISAGREE | AGREE | Only tested stack that caught the wrong-target edit and kept the clean edit green |

## Conclusion

The verifier prompt upgrade is necessary but not sufficient by itself. On the current hardware and model set, the best observed pair for repeated-target safety is `qwen3-coder:30b-coding` with the v1.1.0 prompt draft. The shipped default remains unchanged until a separate approval step flips it.
