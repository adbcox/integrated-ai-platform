# Aider Compute Doctrine
# Deliverable: D-17-97 (Aider compute redirect to Mac Studio M3 Ultra)
# Status: ESTABLISHED 2026-05-04

## Canonical compute target

**Mac Studio M3 Ultra at 192.168.10.142:11434 is the canonical Ollama compute
node for all Aider coding workloads.** This supersedes the prior Mac Mini
(`127.0.0.1:11434`) default established in D-17-94.

Rationale:
- Mac Studio M3 Ultra: 96 GB unified memory — can load 30B+ models without
  swapping; 85 tps on qwen3-coder:30b per D-17-91 benchmark
- Mac Mini M4 Pro: 48 GB unified memory — adequate for fallback/airgap but
  slower on large models; prior default caused timeouts on 14b under load (D-17-97)
- D-17-91 benchmark result: qwen3-coder:30b (T3-B) is the superior model for
  Aider's task class (refactor/tool-call/agentic) at 85 tps vs Mac Mini's
  qwen2.5-coder:14b

## Model cascade (effective D-17-97)

| Slot | Model | Host | Use case |
|------|-------|------|----------|
| Primary | `qwen3-coder:30b` | Mac Studio 192.168.10.142 | Default for all C0/C1/C2/C3 tasks |
| `--hard` | `qwen3-coder-next:latest` | Mac Studio 192.168.10.142 | Multi-paragraph, long-context, timed-out tasks |
| Emergency fallback | `qwen2.5-coder:7b` | Mac Mini 127.0.0.1 | Airgap / Mac Studio unreachable |

**Prior cascade (D-17-94, retired):** qwen2.5-coder:14b → qwen2.5-coder:32b → qwen2.5-coder:7b on Mac Mini.

## Configuration files

- `bin/aider_local.sh`: `API_BASE="${OLLAMA_API_BASE:-http://192.168.10.142:11434}"`, `MODEL="ollama_chat/qwen3-coder:30b"`, `--hard` → `qwen3-coder-next:latest` (timeout 480s)
- `domains/coding.py`: `DEFAULT_MODEL_CASCADE = ["qwen3-coder:30b", "qwen3-coder-next:latest", "qwen2.5-coder:7b"]`
- `config/model_pairs.yaml`: fast_accurate/balanced/thorough pairs updated to qwen3 family

## Mac Mini retention

Mac Mini retains the `qwen2.5-coder` family for:
1. Emergency offline fallback (Mac Studio unreachable, network partition)
2. Provenance gate (`scripts/verify-model-provenance.sh`) — CPU-only kit, runs fine on Mac Mini
3. Goose dispatch sessions (Goose uses its own native Ollama provider, separate from Aider)

Mac Mini is NOT removed from service — it remains the control-plane host.

## Override for Mac Mini

```bash
# Force Mac Mini for a single invocation:
OLLAMA_API_BASE=http://127.0.0.1:11434 scripts/aider-task.sh "task" file.py

# Force Mac Mini in bin/aider_local.sh directly:
OLLAMA_API_BASE=http://127.0.0.1:11434 bin/aider_local.sh --message "task" file.py
```

The `--gpu-experimental` flag in `bin/aider_local.sh` is a legacy alias for Mac Mini
local Ollama (`127.0.0.1:11434`).

## Reachability check

```bash
# Verify Mac Studio Ollama is up:
curl -s http://192.168.10.142:11434/api/tags | python3 -c "import json,sys; m=json.load(sys.stdin); print(f'OK: {len(m[\"models\"])} models')"

# Check loaded models:
ssh 192.168.10.142 "ollama ps"
```

## Relationship to D-17-58 (Mac Studio Ollama LaunchDaemon)

D-17-58 established Mac Studio as the compute node with Ollama running as a
LaunchDaemon at `192.168.10.142:11434`. D-17-97 completes the connection: Aider
now routes to that node by default, fulfilling the architectural intent of D-17-58.

## Relationship to D-17-91 (benchmark)

D-17-91 benchmarked T3-B (`qwen3-coder:30b`) vs T3-C (`qwen3-coder-next:latest`)
on Mac Studio. Key findings used in cascade design:
- T3-B (qwen3-coder:30b): wins refactor/tool-call/agentic (85 tps, comparable accuracy)
- T3-C (qwen3-coder-next): wins long-context (1.00 vs 0.80 mean at lc-CC-prior-art)
- Mapping: T3-B → default slot; T3-C → `--hard` long-context slot

## Chronicle

- D-17-97 established: 2026-05-04. Mac Studio M3 Ultra at 192.168.10.142:11434
  promoted to canonical Aider compute. qwen3-coder:30b as primary, qwen3-coder-next
  as --hard. Smoke test: PASS (`[aider-local] OLLAMA_API_BASE=http://192.168.10.142:11434`,
  model `ollama_chat/qwen3-coder:30b`, edit applied in single pass, exit 0).

## Related docs

- `docs/architecture-facts/goose-capability-boundary.md` — Goose compute posture
- `docs/runbooks/aider-default-workflow.md` — operator workflow (updated D-17-97)
- `docs/phase-17/d-17-91/WP02_RESULTS_2026-05-04.md` — benchmark results
- `docs/architecture-facts/exo-cluster.md` — Mac Studio node chronicle
