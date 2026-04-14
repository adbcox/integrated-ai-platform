Stage RAG-1 Retrieval Helper
============================

Purpose
-------
`bin/stage_rag1_search.py` offers a lightweight lexical/BM25 search over
planning-relevant surfaces (bin/, shell/, docs/, Makefile). It is meant for
Stage-3 planning only: use it to pick the right file and anchor before drafting
a probe, but continue to follow the single-file micro-lane, literal replacement
rules, and validation steps.

Usage
-----
```
bin/stage_rag1_search.py "where remote handoff bundle validation is defined"
```

- `--top N` limits results (default 5).
- `--chunk-size L` / `--overlap O` control line windowing if you need bigger
  snippets for investigation.
- Use `bin/stage_rag1_plan_probe.py` when you want to log the search along with
  the selected file + anchor (Stage-4 boundary requirement).
- Run `bin/stage_rag1_metrics.py --window 40` after a probe battery to see how
  often literal/anchor guard failures appeared in the latest aide runs. The same
  report also reads `artifacts/micro_runs/events.jsonl` so preflight rejections
  (`literal_replace_missing_old`, `literal_shell_risky`,
  `prompt_contract_rejection`, `missing_file_ref`, `missing_anchor`) show up
  next to guard-level failures.

Scope & Filters
---------------
- Indexed: `bin/`, `shell/`, `docs/`, `Makefile`.
- Excluded: `.git/`, `artifacts/`, temp/generated outputs, binary files,
  anything outside Stage-3 planning scope.

Outputs include the file path, line range, and snippet so you can jump straight
to the relevant anchor inside your editor before creating or editing probes.
