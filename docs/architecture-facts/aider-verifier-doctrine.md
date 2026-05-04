# Aider Dual-Loop Verifier Doctrine (D-17-110)

**Status:** DONE — 2026-05-04
**Chronicle scope:** Layer 1.5 verifier — LLM-based diff review inserted between Layer 1 (deletion-rate guard) and Layer 3 (telemetry).

---

## Motivation

**Finding 23 (D-17-109):** A 607-line duplication failure on a 27KB Python file passed Layer 1 (deletion-rate guard) because net deletions were low. The insertion-expansion guard (also D-17-109) catches ratio violations, but a model can duplicate exactly the right amount of code to slip past the ratio check. No automated check was reviewing semantic correctness: *does this diff actually do what the task asked?*

The dual-loop verifier closes this gap by routing the diff through a second, independent LLM that answers a single binary question.

---

## Architecture: Layer 1.5

```
aider-task.sh post-run flow:
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 1 — Diff sanity guard (aider_guard.py)               │
│  deletion-rate check + insertion-expansion check            │
│  EXIT 4 on BLOCK; continues on PASS                         │
└─────────────────────────────────────────────────────────────┘
       │ PASS
       ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 1.5 — Dual-loop verifier (bin/aider_verifier.py)     │
│  LLM reads: task description + diff + function counts       │
│  Classifies: AGREE | DISAGREE | AMBIGUOUS | ERROR           │
│  EXIT 5 on DISAGREE; non-blocking on AMBIGUOUS/ERROR        │
└─────────────────────────────────────────────────────────────┘
       │ AGREE or non-blocking
       ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 3 — Learning telemetry (domains/learning.py)         │
│  Records outcome to artifacts/execution_metrics.jsonl       │
└─────────────────────────────────────────────────────────────┘
```

---

## Model Selection (D-17-110 WP-04 evaluation)

| Model | AGREE accuracy | DISAGREE accuracy | Status |
|---|---|---|---|
| `deepseek-coder-v2:latest` (Mac Mini, base chat) | Good | Poor — hallucinated AGREE on logic-change and duplication | **Rejected** |
| `qwen2.5-coder:14b` (Mac Mini, instruct) | Good | Good — caught both logic-change and duplication | **Selected (default)** |
| `deepseek-coder-v2:16b-lite-instruct-q4_K_M` (Mac Studio) | Not tested externally | Candidate | When D-17-109 WP-03 LaunchDaemon lands |

**Root cause of base-model failure:** `deepseek-coder-v2:latest` uses `User:` / `Assistant:` stop tokens and `/api/chat` messages format produces garbage output (math problems). Even with `/api/generate` and raw prompting, the base model tends to AGREE regardless of diff content — insufficient instruction following. Instruct models required.

**Env overrides:**
```bash
AIDER_VERIFIER_MODEL=deepseek-coder-v2:16b-lite-instruct-q4_K_M  # switch to Mac Studio
AIDER_VERIFIER_API_BASE=http://192.168.10.142:11434               # when Mac Studio WP-03 lands
AIDER_VERIFIER_TIMEOUT=60                                          # seconds (default)
```

---

## Verdict Semantics

| Verdict | Meaning | aider-task.sh action |
|---|---|---|
| `AGREE` | Diff matches task description — nothing more, nothing less | Continue to Layer 3 + commit hint |
| `DISAGREE` | Diff diverges from task — duplication, logic change, or scope creep | Exit 5; block commit |
| `AMBIGUOUS` (exit 3) | Model responded but verdict unparseable | Non-blocking; print warning; continue |
| `ERROR` (exit 2) | Model unreachable or API failure | Non-blocking; print warning; continue |

**Non-blocking design rationale:** verifier failure must not prevent legitimate Aider work. An unreachable Ollama endpoint, timeout, or parse error prints a warning and allows the operator to proceed. The verifier is advisory; Layer 1 deletion-rate guard is the hard gate.

---

## What AGREE/DISAGREE Signals

**AGREE signals:** The verifier checked:
- Function/class count was stable (unless task explicitly adds/removes functions)
- No function bodies were duplicated in the diff
- Code logic was not modified beyond the stated task scope
- Changes are proportional to the task description

**DISAGREE signals — operator must:**
1. Review the printed REASON (one sentence, ≤120 chars)
2. Run `git diff <files>` to inspect the actual changes
3. Decide: revert with `git checkout <file>` or override with `--skip-verifier`
4. If overriding because the verifier is wrong (false positive): note it — this informs future prompt refinement

---

## What the Verifier Does NOT Catch

- Correctness of logic within the stated scope (e.g., wrong algorithm, off-by-one error)
- Style guide violations
- Security issues
- Performance regressions
- Test coverage gaps

The verifier answers only "does this match the task?" not "is this correct?"

---

## Bypass Ladder

| Override | Scope | Use when |
|---|---|---|
| `--skip-verifier` | Layer 1.5 only | Known-good diff, verifier false positive, or verifier too slow |
| `AIDER_SKIP_VERIFIER=1` | Layer 1.5 (env) | Pipeline invocations, batch runs |
| `--skip-validator` | Layer 1 only | Layer 1 deletion-rate is too conservative |
| Both combined | All guards | Emergency: known-good large refactor |

---

## Prompt Template

`config/prompts/library/v1.0.0/07-deepseek-verifier-prompt.md`

Template variables: `{description}`, `{file_path}`, `{diff}`, `{original_function_count}`, `{new_function_count}`

The prompt uses a raw `/api/generate` call (not `/api/chat`) with a primed `VERDICT:` suffix to force two-line structured output. Temperature is forced to 0.0 for deterministic classification.

---

## Logging

Events logged to `artifacts/aider_runs/verifier_events.jsonl` (append-only):
```json
{
  "timestamp": "2026-05-04T...",
  "description": "...",
  "file_path": "...",
  "verdict": "AGREE|DISAGREE|ERROR|AMBIGUOUS",
  "reason": "...",
  "model_response_raw": "...(first 500 chars)",
  "duration_sec": 3.6,
  "orig_count": 5,
  "new_count": 5,
  "model": "qwen2.5-coder:14b"
}
```

---

## Relationship to Finding 23

Finding 23 (D-17-109) identified that the insertion-expansion guard misses duplications where the ratio stays below threshold. The verifier is a semantic complement:

- **Layer 1 guard:** catches deletion-rate anomalies + insertion-expansion ratio anomalies
- **Layer 1.5 verifier:** catches semantic mismatches — duplication, scope creep, logic rewrites

Together they cover the failure modes that caused the 607-line duplication to slip through.

---

## Mac Studio DeepSeek Model (WP-02 record)

`deepseek-coder-v2:16b-lite-instruct-q4_K_M` pulled to Mac Studio 2026-05-04:
- **Digest (sha256[:12]):** `dac6ff6589c9`
- **Size:** 10 GB
- **Architecture:** `deepseek2`
- **Mac Studio footprint after pull:** 51+18+15+10 = 94 GB (within 96 GB capacity)
- **Provenance:** `scan-failed` (scan_rc=137, OOM during fingerprint scan)
  - Same pattern as `Qwen/Qwen3-Coder-30B-A3B-Instruct` (scan_rc=137)
  - Accepted under operator risk acceptance per model-provenance-doctrine.md precedent
  - Chronicle: `docs/_provenance/deepseek-ai__DeepSeek-Coder-V2-Lite-Instruct.json`
- **Activation path:** Set `AIDER_VERIFIER_API_BASE=http://192.168.10.142:11434` + `AIDER_VERIFIER_MODEL=deepseek-coder-v2:16b-lite-instruct-q4_K_M` after D-17-109 WP-03 LaunchDaemon loads on Mac Studio

---

## Cross-references

- **D-17-109** — Layer 1 insertion-expansion guard (Finding 23); system context injection; Modelfile derivations
- **D-17-103** — Three-layer intelligence system (Layers 1, 2, 3)
- **Finding 23** — 607-line duplication failure that motivated Layer 1.5
- **D-17-92** — Model provenance doctrine (scan-failed/OOM precedent)
- `bin/aider_verifier.py` — verifier implementation
- `config/prompts/library/v1.0.0/07-deepseek-verifier-prompt.md` — prompt template
- `artifacts/aider_runs/verifier_events.jsonl` — event log
- `docs/phase-17/d-17-110/SMOKE_2026-05-04.md` — smoke test results
