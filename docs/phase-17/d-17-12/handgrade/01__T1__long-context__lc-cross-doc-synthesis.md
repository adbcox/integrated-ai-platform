# Hand-grade packet 01 — T1 long-context lc-cross-doc-synthesis

**Run:** 20260503T170223Z
**Model:** qwen2.5-coder:32b on mac-mini
**Workload:** long-context
**Task ID:** lc-cross-doc-synthesis

## Auto-grader output

- score: **0.6**
- pass: **False**
- notes: 3/5 expected facts present
- wall_s: 423.5839763329999, tps: 8.612505297430792

## Task summary

Synthesize across both documents — what does Finding 1 tool-call gap have to do with exo's Finding S?

## Model response (full)

```
Finding S and Finding DD in Document A are related in the context of the Open WebUI's integration with the exo cluster via the OpenAI-compatible API path. Specifically, both findings highlight issues related to environment variable settings and diagnostic procedures that led to incorrect conclusions about the operational state of the system.

### Finding S:
- **Description:** The Open WebUI's `OPENAI_API_KEY` was empty (length=1; SHA-256 matches the empty-string hash). This path had not been exercised because Open WebUI used a direct path for local models and never utilized the OpenAI-compatible client.
- **Resolution Date:** Resolved during D-17-26 close.
- **Commit Reference:** Not explicitly mentioned, but the resolution is described in the document.

### Finding DD:
- **Description:** A diagnostic trap where `docker exec <container> sh -c 'echo $VAR'` returns values from `Config.Env` (image-baked + compose-passed env), not from PID 1's actual runtime environ. This led to incorrect conclusions about the presence of credentials.
- **Resolution Date:** Discovered and resolved during D-17-26 close.
- **Commit Reference:** Not explicitly mentioned, but the resolution is described in the document.

### Relationship:
Finding S initially indicated that the `OPENAI_API_KEY` was effectively empty, which led to the assumption that the Open WebUI's OpenAI-compatible client path was broken. However, this conclusion was based on a diagnostic procedure (Finding DD) that did not correctly inspect the runtime environment of the container.

Specifically:

1. **Incorrect Diagnostic Procedure:** During D-17-26 close, the diagnostic command `docker exec <container> sh -c 'echo $OPENAI_API_KEY'` returned an empty string, leading to the conclusion that the `OPENAI_API_KEY` was not set.

2. **Correct Diagnostic Procedure:** The correct method to inspect environment variables in a running container is to query `/proc/1/environ`. This revealed that the `OPENAI_API_KEY` was actually present and correctly configured.

3. **Resolution:** The diagnostic error (Finding DD) was identified, and it clarified that the initial conclusion about the broken path (Finding S) was incorrect. The wiring between Open WebUI and the exo cluster via the OpenAI-compatible API was operational all along.

### Specific Dates or Commit References:
- **D-17-26 Close Date:** 2026-05-03
- **Commit Reference for Finding DD Resolution:** Not explicitly provided, but described in the document as part of D-17-26 closeout.
- **Commit Reference for Finding S Resolution:** Not explicitly provided, but described in the document as part of D-17-26 closeout.

In summary, both findings were resolved during the closeout of D-17-26 on 2026-05-03. The resolution of Finding DD clarified that the diagnostic procedure used for Finding S was flawed, leading to an incorrect conclusion about the operational state of the Open WebUI's OpenAI-compatible client path.
```

## Operator scoring

- [ ] coherent? (yes / no)
- [ ] addresses task? (yes / partial / no)
- [ ] ship-ready quality? (yes / no)
- [ ] auto-grade fair? (yes / too-low / too-high) — by how much?
- [ ] hand-grade 0.00-1.00: ___
- [ ] notes:
