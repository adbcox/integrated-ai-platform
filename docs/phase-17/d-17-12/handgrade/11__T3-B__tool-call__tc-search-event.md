# Hand-grade packet 11 — T3-B tool-call tc-search-event

**Run:** 20260503T180613Z
**Model:** qwen3-coder:30b on mac-studio
**Workload:** tool-call
**Task ID:** tc-search-event

## Auto-grader output

- score: **0.6**
- pass: **False**
- notes: called search_web (structured); 0/1 args match
- wall_s: 0.5148228329999824, tps: 91.01030033849108

## Task summary

Pick web search for current-events query

## Model response (full)

```

```

## Structured tool_calls (Ollama-emitted)

```json
[
  {
    "id": "call_knkv9fca",
    "function": {
      "index": 0,
      "name": "search_web",
      "arguments": {
        "query": "Apple M5 chip release news",
        "max_results": 5
      }
    }
  }
]
```

## Operator scoring

- [ ] coherent? (yes / no)
- [ ] addresses task? (yes / partial / no)
- [ ] ship-ready quality? (yes / no)
- [ ] auto-grade fair? (yes / too-low / too-high) — by how much?
- [ ] hand-grade 0.00-1.00: ___
- [ ] notes:
