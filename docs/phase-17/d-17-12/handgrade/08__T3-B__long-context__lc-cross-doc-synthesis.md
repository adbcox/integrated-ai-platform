# Hand-grade packet 08 — T3-B long-context lc-cross-doc-synthesis

**Run:** 20260503T180613Z
**Model:** qwen3-coder:30b on mac-studio
**Workload:** long-context
**Task ID:** lc-cross-doc-synthesis

## Auto-grader output

- score: **0.8**
- pass: **True**
- notes: 4/5 expected facts present
- wall_s: 61.29048716700001, tps: 44.85702410665291

## Task summary

Synthesize across both documents — what does Finding 1 tool-call gap have to do with exo's Finding S?

## Model response (full)

```
Based on the provided documents (exo cluster and integration audit), here's how Finding S and Finding DD are related in the closeout of D-17-26:

1.  **Finding S (Open WebUI Wiring):** This finding, documented in the exo cluster architecture fact (Document A), identified a latent issue where the Open WebUI's OpenAI-compatible client path was "unwired." Specifically, the `OPENAI_API_KEY` environment variable inside the Open WebUI container was empty (length=1, matching the SHA-256 hash of an empty string). This was because Open WebUI was using the Ollama direct path for local models and had never exercised the OpenAI-compatible client path. The finding concluded that wiring required a Vault-Agent sidecar deliverable (provisional D-17-26).

2.  **D-17-26 Closeout:** The D-17-26 deliverable was explicitly scoped to address Finding S, aiming to wire the Open WebUI to the exo route via Vault-Agent sidecar. However, the closeout of D-17-26 (as described in Document A) revealed a crucial correction:
    *   **Finding DD Diagnostic Trap:** The initial diagnosis of the "unwired" state (as described in D-17-14 WP-06, which corresponds to Finding S's premise) was incorrect. Finding DD, documented in Document A, describes a diagnostic trap where inspecting container environment variables using `docker exec <container> sh -c 'echo $VAR'` returns the value from `Config.Env` (image-baked) rather than the actual runtime environment (`/proc/1/environ`). This led to the false conclusion that `OPENAI_API_KEY` was effectively empty.
    *   **Correct Diagnosis:** The actual investigation, conducted during D-17-26 (taking about 25 minutes), revealed that the plumbing was *operational* the whole time. The `OPENAI_API_KEY` was correctly set (length=67, matching the `LITELLM_MASTER_KEY` fingerprint) in the runtime environment (`/proc/1/environ`), and the end-to-end path from Open WebUI → litellm → exo was functional, returning HTTP 200 for the `exo-qwen-coder-7b` model.

3.  **Resolution:** The closeout of D-17-26 explicitly states: "**CLOSED no-fix-needed with doctrine finding:** the wiring was operational the whole time; the broken-state premise was a Finding-DD diagnostic error." This means that while D-17-26 was *intended* to fix the issue described in Finding S (the unwired path), the actual root cause was the diagnostic error described in Finding DD. The "fix" was not a code change but a correction of the diagnosis, confirming that the integration was already working.

In summary, Finding S identified a potential integration gap (unwired Open WebUI), but the closeout of D-17-26 (2026-05-03) revealed that the gap was not real due to a diagnostic error (Finding DD). The D-17-26 closeout explicitly states that the wiring was operational, resolving the issue by correcting the misdiagnosis rather than implementing a fix. The specific date of the D-17-26 closeout is 2026-05-03, and the commit reference for the D-17-26 closeout is mentioned as being part of the "doctrine finding" referenced in the exo cluster document.
```

## Operator scoring

- [ ] coherent? (yes / no)
- [ ] addresses task? (yes / partial / no)
- [ ] ship-ready quality? (yes / no)
- [ ] auto-grade fair? (yes / too-low / too-high) — by how much?
- [ ] hand-grade 0.00-1.00: ___
- [ ] notes:
