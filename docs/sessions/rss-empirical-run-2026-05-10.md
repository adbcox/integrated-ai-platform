# RSS Empirical Run Session — Blocked on Prototype Configuration (2026-05-10)

## Scope

Attempt to run RSS prototype empirical validation against the stunt-double-backed LiteLLM proxy infrastructure.

## Preflight Status

✓ Stunt-double deployment operational (feat/track-1a-stunt-double)
✓ LiteLLM proxy running on port 4000
✓ Tier-1 Ollama (localhost:11434), Tier-2 stunt-double (localhost:11435), both responding
✓ E2E proxy smoke test passing

## Blocker

**Prototype cannot run against LiteLLM proxy without source code changes.**

**File:** `prototypes/rss-fetcher/ollama_score.py`, line 29
**Issue:** `OLLAMA_URL = "http://localhost:11434/api/generate"` is hardcoded constant

**Why it matters:**
- Prototype calls direct Ollama `/api/generate` endpoint
- LiteLLM proxy expects `/v1/chat/completions` (OpenAI API)
- Requires: env var reading (code change) + API format translation (code change) + auth header (code change)
- All three violate scope constraint

## Scope Decision

Per hard rules Case C: "Code change is out of scope."

Session ends here. Artifacts documented in `/Users/adriancox/local-ai-workstation/agent_runs/rss_20260510_000337/`:
- `inventory.md` — prototype structure and defect summaries
- `failure_state.md` — detailed blocker analysis
- `FINDINGS_at_run_time.md` — full FINDINGS.md snapshot at run time

## Next Session Options

**Option A:** Make RSS prototype endpoint configurable via env var (code change, separate session)
- Would enable running RSS prototype through any endpoint (direct Ollama, LiteLLM, or remote)
- Defect 1 analysis still valid with direct Ollama

**Option B:** Run prototype as-is against localhost:11434
- Empirical validation of Defect 1 (tool-name pre-pass) doesn't require proxy
- Defect is in rubric/model behavior, not infrastructure
- Simpler: no code changes, just execute

**Option C:** Write minimal adapter script
- Translate prototype's Ollama API calls to LiteLLM format
- Validates proxy stack in production shape
- Infrastructure validation only, separate from Defect 1 analysis

## Recommendation

If **goal is Defect 1 empirical data:** choose Option B (run as-is).
If **goal is proxy validation:** choose Option C (adapter script).
If **goal is general robustness:** choose Option A (make configurable).

Operator's intent will determine which path next session takes.
