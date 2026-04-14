# Stage-5 Operator Guide (April 2026)

Stage 5 introduces **bounded dual-target literal batches**. Use it when you need
to apply up to two synchronized literal/comment edits in a single commit while
keeping the Stage-4 guardrails (literal templates, automatic quick checks, and
rollback on failure).

## Promoted Stage-5 class

- Up to **two entries per batch** (JSON file consumed by `bin/stage5_manager.py`).
- Each entry follows the Stage-4 literal template (3–8 contiguous lines,
  shell/bin targets, no harness files).
- Stage-5 orchestrates the edits atomically: if any entry fails, the repo is
  restored to the starting HEAD.
- A single commit is produced once all entries succeed, so documentation/test
  updates referencing both files may merge together.
- Planning is performed with **Stage RAG-3** which augments Stage RAG-2
  structural hits with related-file suggestions suitable for multi-file batches.
- Manager-4 can now auto-build the JSON batch for you: supply the first literal
  via `--query/--target/--message` plus optional `--secondary-*` flags and route
  with `--stage stage5`. The dispatcher writes a temporary batch file in `/tmp`
  and pipes it directly into `bin/stage5_manager.py`.

## Workflow

1. Prepare a JSON batch file with one or two entries:
   ```json
   [
     {
       "query": "tighten detection priority comment",
       "target": "bin/detect_changed_files.sh",
       "message": "bin/detect_changed_files.sh::priority comment replace exact text '...' with '...' only.",
       "lines": "1-8",
       "notes": "stage5 op 1"
     },
     {
       "query": "remote finalize hint",
       "target": "bin/remote_finalize.sh",
       "message": "bin/remote_finalize.sh::usage comment replace exact text '...' with '...' only."
     }
   ]
   ```
2. Run Stage-5 manager:
   ```sh
   python3 bin/stage5_manager.py \
     --batch-file path/to/batch.json \
     --commit-msg "stage5: sync detection/finalize hints"
   ```
   The manager logs Stage RAG-3 plans for each entry, routes to Stage-4 manager
   in `--no-commit` mode, captures per-entry diff stats, and commits once at the
   end if all edits succeed. Operation details (plan IDs, files, add/delete
   counts) now land in `artifacts/stage5_manager/traces.jsonl`.
3. Monitor traces under `artifacts/stage5_manager/traces.jsonl`.

## Safety and rollback

- The manager captures the starting `HEAD` and restores it automatically if any
  entry fails (including literal guards, placeholder violations, or worker exit).
- Stage-4 guardrails still execute for each entry; Stage-5 simply batches them.
- Diff budgets:
  - per entry: enforced by Stage-4 manager (≤12 lines).
  - per batch: Stage-5 aborts if combined `add+delete` exceeds 20 lines.

## When not to use Stage-5

- Structural/multi-file edits that require shell-control changes.
- Docs/README edits (still outside the literal lane).
- Larger batches; keep Stage-5 to "two coordinated literal changes" until we
  finish validating multi-target rollback.
