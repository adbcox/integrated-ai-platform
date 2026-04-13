# Safe Literal Probe Helper

Use this helper whenever you want to stay inside the **Stage 3 fast micro lane**, which now covers:

- anchored literal wording edits (up to two adjacent lines)
- anchored single-line comment edits
- single shell/bin target files
- immediate commit (or rollback) before the next probe
- literal fallback + rollback protections intact
- Stage RAG-1 logging before every literal probe so anchor selection is recorded

## Quick steps

1. Copy the template to a scratch message file:
   ```sh
   cp templates/safe-literal-probe-template.msg /tmp/probe_literal.msg
   ```
2. Edit the message so it anchors the exact file + literal you want to touch. Every message should:
   - name the file using `path/to/file.sh::short anchor`
   - say `replace exact text 'old' with 'new'` (or `update comment`, etc.)
   - end with `only. one replacement only. no behavior change.` unless you have a more precise literal note
3. Run the micro helper, pointing it at the message file and exactly one target file:
   ```sh
   make aider-micro-safe \
     AIDER_MICRO_MESSAGE_FILE=/tmp/probe_literal.msg \
     AIDER_MICRO_FILES="bin/quick_check.sh"
   ```

## Example

```
bin/quick_check.sh::status text replace exact text "echo \"[quick] Detecting changed files...\"" with "echo \"[quick] Checking for changed files...\"" only. one replacement only. no behavior change.
```

Pair every literal probe with an immediate `git status` + commit (or rollback) before launching the next probe.

## Stage RAG-1 planning hook (Stage 3 / Stage 4)

Before editing the template, record the file + anchor via the retrieval helper:

```sh
bin/stage_rag1_plan_probe.py --stage stage4 \
  --plan-id "stage4-boundary-$(date +%Y%m%d-%H%M)" \
  --top 6 -- "where the literal replace should land"
```

Pick the chunk you intend to edit, enter the repo-relative file path and line
range when prompted, and optionally note anything special (e.g. "expect
literal_replace fallback"). The helper stores the event in
`artifacts/stage_rag1/usage.jsonl`, letting us correlate Stage-4 runs with
`literal_replace_missing_old`, `missing_file_ref`, and `missing_anchor`
failures surfaced by the guard.

### Regression pack

To replay accepted literal/comment probes plus the rejection paths (literal miss, shell-control guard, aider-exit guard), run:

```sh
bin/micro_lane_regression.sh
```

The script uses the templates under `regressions/micro_lane_stage3/messages/` and automatically reverts accepted edits so the repository remains clean.

For quick repo-aware planning context, run:

```sh
bin/micro_repo_context.sh path/to/file.sh
```

which prints `git status` plus the first few lines (default 80) of each requested file.

### Next promotion boundary

Stage 4 work will only start after we can consistently run the regression pack. The likely next boundary is **multi-line literal/comment edits inside a single file**. Do **not** attempt broader scopes until new evidence is captured.
