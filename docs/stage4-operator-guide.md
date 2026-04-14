# Stage-4 Operator Guide (April 2026)

Stage 4 is now open for **bounded multi-line literal edits**. The class sits
between the Stage-3 micro lane (≤2 lines) and the future Stage-5 broader lane.
Use it when a literal/comment change touches **3–8 adjacent lines** inside a
single shell/bin file.

## Promoted Stage-4 class

- Single file under `bin/` or `shell/`.
- Message must follow the literal template ("replace exact text 'old' with 'new'")
  so the guard can enforce precise intent.
- The `old`/`new` quoted blocks may span 3–8 contiguous lines. The manager rejects
  spans outside that window.
- Only one replacement per job. Stage-4 manager enforces `diff_added + diff_deleted ≤ 12`.
- All probes must be planned via **Stage RAG-2** so the anchors include the wider
  function/block context needed for multi-line work.
- Jobs are routed through the local worker via `make aider-micro-safe` with
  `AIDER_MICRO_STAGE=stage4`, so fallback, validation, and rollback protections
  remain intact.

## Workflow

1. **Plan** with Stage RAG-2:
   ```sh
   python3 bin/stage_rag2_plan_probe.py --plan-id stage4-<ticket> --top 6 -- "describe block edit"
   ```
2. **Dispatch** via Manager-3 (auto-detects Stage 3 vs Stage 4):
   ```sh
   python3 bin/manager3.py \
     --query "tighten deploy block" \
     --target bin/aider_loop.sh \
     --message "bin/aider_loop.sh::deploy block replace exact text '...old block...' with '...new block...' only. one replacement only. stage-4 multi-line literal." \
     --commit-msg "stage4: tighten deploy block"
   ```
3. Manager-3 inspects the literal span, routes the job to `bin/stage4_manager.py`,
   and records a trace row under `artifacts/stage4_manager/traces.jsonl` and
   `artifacts/manager3/traces.jsonl`.
4. Stage-4 manager verifies that the literal exists, runs Stage RAG-2 logging,
   launches the worker, enforces diff budgets, and commits on success.

## Safety & rollback

- Stage-4 manager automatically reverts the file if the diff exceeds the
  configured limit and leaves no commits behind.
- The local worker (via `aider_micro.sh`) still runs `make quick` and literal
  fallbacks, so the new class inherits the same guardrails as Stage 3.
- Plan IDs and stage tags are logged in `artifacts/stage_rag2/usage.jsonl` for
  future promotion reviews.

## When not to use Stage 4

- Multi-file edits or shell-control changes (still rejection-only boundary tests).
- Literal spans <3 lines → stay in Stage 3.
- Refactors or structural changes that cannot be described as a single literal
  replacement → escalate to Codex/manual path.

Follow this guide together with `docs/stage3-operator-flow.md` and the Stage-4
entries inside `docs/stage4-readiness-log.md`.
