#!/usr/bin/env python3
"""Build operator hand-grade packets from WP-05 result JSON.

12 selected (model, workload, task) cells — see WP05_RESULTS_2026-05-03.md
"Hand-grade sample" table for rationale.

Each packet:
  handgrade/<NN>__<MODEL>__<WORKLOAD>__<TASK>.md

Format:
  - Task prompt (truncated if huge)
  - Auto-grader output (score, pass, notes)
  - Model response_content (full)
  - Operator scoring rubric:
      [ ] coherent? (yes/no)
      [ ] addresses task? (yes/no/partial)
      [ ] would you ship this? (yes/no)
      [ ] auto-grade fair? (yes/too-low/too-high)
      [ ] hand-grade 0-1
      [ ] notes
"""
from __future__ import annotations
import json, os, sys
from pathlib import Path

ROOT = Path('/Users/admin/repos/integrated-ai-platform/docs/phase-17/d-17-12')
RESULTS = ROOT / 'results'
OUT = ROOT / 'handgrade'

# (run_id, model, workload, task_id, sample_idx)
SAMPLES = [
    ('20260503T170223Z', 'T1', 'long-context', 'lc-cross-doc-synthesis'),
    ('20260503T170223Z', 'T1', 'agentic',      'ag-debug-failing-test'),
    ('20260503T170223Z', 'T2', 'long-context', 'lc-finding-CC-prior-art'),
    ('20260503T170223Z', 'T2', 'agentic',      'ag-debug-failing-test'),
    ('20260503T180613Z', 'T3-A', 'long-context', 'lc-short-gemma-friendly'),
    ('20260503T170223Z', 'T3-A', 'agentic',      'ag-debug-failing-test'),
    ('20260503T170223Z', 'T3-A', 'agentic',      'ag-incident-response'),
    ('20260503T180613Z', 'T3-B', 'long-context', 'lc-cross-doc-synthesis'),
    ('20260503T180613Z', 'T3-B', 'long-context', 'lc-finding-CC-prior-art'),
    ('20260503T170223Z', 'T3-B', 'agentic',      'ag-debug-failing-test'),
    ('20260503T180613Z', 'T3-B', 'tool-call',    'tc-search-event'),
    ('20260503T180613Z', 'T3-B', 'refactor',     'refactor-add-logging'),
]

def load_sample(run_id, model_key, workload, task_id):
    p = RESULTS / run_id / f'{model_key}__{workload}.json'
    d = json.load(open(p))
    for s in d.get('samples', []):
        if s.get('task_id') == task_id:
            return d, s
    raise SystemExit(f'task {task_id} not found in {p}')

def trunc(s, n):
    if s is None: return ''
    return s if len(s) <= n else s[:n] + '...[truncated ' + str(len(s)-n) + ' chars]'

def build_packet(idx, run_id, model_key, workload, task_id):
    rec, sample = load_sample(run_id, model_key, workload, task_id)
    grade = sample.get('grade', {}) or {}
    out = []
    out.append(f'# Hand-grade packet {idx:02d} — {model_key} {workload} {task_id}')
    out.append('')
    out.append(f'**Run:** {run_id}')
    out.append(f'**Model:** {rec.get("model_name","?")} on {rec.get("model_host","?")}')
    out.append(f'**Workload:** {workload}')
    out.append(f'**Task ID:** {task_id}')
    out.append('')
    out.append('## Auto-grader output')
    out.append('')
    out.append(f'- score: **{grade.get("score","?")}**')
    out.append(f'- pass: **{grade.get("pass","?")}**')
    out.append(f'- notes: {grade.get("notes","")}')
    out.append(f'- wall_s: {sample.get("wall_s","?")}, tps: {sample.get("tokens_per_sec","?")}')
    out.append('')
    out.append('## Task summary')
    out.append('')
    out.append(sample.get('task_summary','(none)'))
    out.append('')
    out.append('## Model response (full)')
    out.append('')
    out.append('```')
    out.append(trunc(sample.get('response_content',''), 12000))
    out.append('```')
    out.append('')
    if sample.get('tool_calls'):
        out.append('## Structured tool_calls (Ollama-emitted)')
        out.append('')
        out.append('```json')
        out.append(json.dumps(sample.get('tool_calls'), indent=2))
        out.append('```')
        out.append('')
    out.append('## Operator scoring')
    out.append('')
    out.append('- [ ] coherent? (yes / no)')
    out.append('- [ ] addresses task? (yes / partial / no)')
    out.append('- [ ] ship-ready quality? (yes / no)')
    out.append('- [ ] auto-grade fair? (yes / too-low / too-high) — by how much?')
    out.append('- [ ] hand-grade 0.00-1.00: ___')
    out.append('- [ ] notes:')
    out.append('')
    return '\n'.join(out)

def main():
    OUT.mkdir(exist_ok=True)
    for i, (run_id, mk, wl, tid) in enumerate(SAMPLES, 1):
        try:
            packet = build_packet(i, run_id, mk, wl, tid)
        except SystemExit as e:
            print(f'  packet {i:02d}: SKIP — {e}')
            continue
        fn = OUT / f'{i:02d}__{mk}__{wl}__{tid}.md'
        fn.write_text(packet)
        print(f'  packet {i:02d}: wrote {fn.name}')
    print('\nbuilt', i, 'packets')

if __name__ == '__main__':
    main()
