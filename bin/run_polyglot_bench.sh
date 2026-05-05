#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BENCH_ROOT="${POLYGLOT_BENCH_ROOT:-/Users/admin/aider-polyglot-bench}"
ARTIFACT_ROOT="$REPO_ROOT/artifacts/polyglot_bench"
MODEL=""
TASK_SUBSET=""
KEYWORDS=""
LANGUAGES=""
OLLAMA_DIRECT_BASE="${OLLAMA_API_BASE:-http://192.168.10.142:11434}"
OLLAMA_BASE="$OLLAMA_DIRECT_BASE"
TUNNEL_PID=""
TUNNEL_PORT=""
# D-17-134: raised defaults to survive large-model latency
BENCH_TIMEOUT="${BENCH_TIMEOUT:-1800}"   # per-task timeout seconds (AIDER_TIMEOUT)
BENCH_TRIES="${BENCH_TRIES:-2}"          # max retries per task (--tries)
FULL_RUN=0                               # set by --full; overrides --task-subset

usage() {
  cat <<'USAGE'
Usage:
  bin/run_polyglot_bench.sh --model <model> [--task-subset N] [--full] [--keywords k1,k2] [--languages l1,l2]

Options:
  --model <name>         Model name passed to aider benchmark (required)
  --task-subset <N>      Limit to N benchmark tasks for a shorter run
  --full                 Run all tasks (ignores --task-subset)
  --keywords <list>      Comma-separated benchmark keyword filter
  --languages <list>     Comma-separated language filter
  --ollama-base <url>    Override Ollama base URL passed to the container
  --no-tunnel            Skip the automatic SSH tunnel to Mac Studio
  --timeout <secs>       Per-task timeout in seconds (default: 1800, env: BENCH_TIMEOUT)
  --tries <N>            Max retries per task (default: 2, env: BENCH_TRIES)
USAGE
}

sanitize_name() {
  printf '%s' "$1" | tr '/: ' '___' | tr -cd 'A-Za-z0-9._-'
}

pick_tunnel_port() {
  local port
  for port in 11435 11436 11437 11438 11439; do
    if ! lsof -ti tcp:"$port" >/dev/null 2>&1; then
      printf '%s' "$port"
      return 0
    fi
  done
  return 1
}

start_tunnel() {
  TUNNEL_PORT="$(pick_tunnel_port)" || {
    echo "ERROR: no free SSH tunnel port found in 11435-11439" >&2
    exit 1
  }
  ssh -o ExitOnForwardFailure=yes -N -L "${TUNNEL_PORT}:127.0.0.1:11434" admin@192.168.10.142 &
  TUNNEL_PID="$!"
  trap cleanup EXIT INT TERM
  export OLLAMA_BASE="http://host.docker.internal:${TUNNEL_PORT}"
}

cleanup() {
  if [[ -n "${TUNNEL_PID:-}" ]]; then
    kill "$TUNNEL_PID" >/dev/null 2>&1 || true
  fi
}

MODEL_SET=0
TASK_SUBSET_SET=0
NO_TUNNEL=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)
      [[ $# -ge 2 ]] || { echo "ERROR: --model requires a value" >&2; exit 1; }
      MODEL="$2"; MODEL_SET=1; shift 2 ;;
    --model=*)
      MODEL="${1#--model=}"; MODEL_SET=1; shift ;;
    --task-subset)
      [[ $# -ge 2 ]] || { echo "ERROR: --task-subset requires a value" >&2; exit 1; }
      TASK_SUBSET="$2"; TASK_SUBSET_SET=1; shift 2 ;;
    --task-subset=*)
      TASK_SUBSET="${1#--task-subset=}"; TASK_SUBSET_SET=1; shift ;;
    --full)
      FULL_RUN=1; shift ;;
    --keywords)
      [[ $# -ge 2 ]] || { echo "ERROR: --keywords requires a value" >&2; exit 1; }
      KEYWORDS="$2"; shift 2 ;;
    --keywords=*)
      KEYWORDS="${1#--keywords=}"; shift ;;
    --languages)
      [[ $# -ge 2 ]] || { echo "ERROR: --languages requires a value" >&2; exit 1; }
      LANGUAGES="$2"; shift 2 ;;
    --languages=*)
      LANGUAGES="${1#--languages=}"; shift ;;
    --ollama-base)
      [[ $# -ge 2 ]] || { echo "ERROR: --ollama-base requires a value" >&2; exit 1; }
      OLLAMA_DIRECT_BASE="$2"; OLLAMA_BASE="$2"; shift 2 ;;
    --ollama-base=*)
      OLLAMA_DIRECT_BASE="${1#--ollama-base=}"; OLLAMA_BASE="$OLLAMA_DIRECT_BASE"; shift ;;
    --no-tunnel)
      NO_TUNNEL=1; shift ;;
    --timeout)
      [[ $# -ge 2 ]] || { echo "ERROR: --timeout requires a value" >&2; exit 1; }
      BENCH_TIMEOUT="$2"; shift 2 ;;
    --timeout=*)
      BENCH_TIMEOUT="${1#--timeout=}"; shift ;;
    --tries)
      [[ $# -ge 2 ]] || { echo "ERROR: --tries requires a value" >&2; exit 1; }
      BENCH_TRIES="$2"; shift 2 ;;
    --tries=*)
      BENCH_TRIES="${1#--tries=}"; shift ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "ERROR: unknown option '$1'" >&2; usage >&2; exit 1 ;;
  esac
done

[[ -n "$MODEL" ]] || { echo "ERROR: --model is required" >&2; exit 1; }
[[ -d "$BENCH_ROOT" ]] || { echo "ERROR: benchmark root not found: $BENCH_ROOT" >&2; exit 1; }

if [[ "$NO_TUNNEL" -eq 0 && "$OLLAMA_DIRECT_BASE" == "http://192.168.10.142:11434" ]]; then
  start_tunnel
fi

MODEL_SLUG="$(sanitize_name "$MODEL")"
STAMP="$(date +%F)"
# --full overrides any --task-subset
[[ $FULL_RUN -eq 1 ]] && TASK_SUBSET=""
# Build run tag: include subset count if a subset is being run
if [[ -n "$TASK_SUBSET" ]]; then
  RUN_TAG="${MODEL_SLUG}_${STAMP}_subset${TASK_SUBSET}"
else
  RUN_TAG="${MODEL_SLUG}_${STAMP}_full"
fi
RUN_DIR_GLOB="$BENCH_ROOT/tmp.benchmarks/*--$RUN_TAG"
RESULT_JSON="$ARTIFACT_ROOT/${RUN_TAG}.json"

mkdir -p "$ARTIFACT_ROOT"

DOCKER_ARGS=(
  run --rm
  --add-host=host.docker.internal:host-gateway
  -e AIDER_DOCKER=1
  -e AIDER_BENCHMARK_DIR=/benchmarks
  -e OLLAMA_API_BASE="$OLLAMA_BASE"
  -e AIDER_TIMEOUT="$BENCH_TIMEOUT"
  -v "$BENCH_ROOT:/aider"
  -v "$BENCH_ROOT/tmp.benchmarks:/benchmarks"
  -w /aider
  aider-benchmark
  bash -lc
)

BENCH_CMD=(
  "python3" "./benchmark/benchmark.py" "$RUN_TAG"
  "--new"
  "--model" "$MODEL"
  "--edit-format" "diff"
  "--threads" "1"
  "--tries" "$BENCH_TRIES"
)
if [[ -n "$TASK_SUBSET" ]]; then
  BENCH_CMD+=("--num-tests" "$TASK_SUBSET")
fi
if [[ -n "$KEYWORDS" ]]; then
  BENCH_CMD+=("--keywords" "$KEYWORDS")
fi
if [[ -n "$LANGUAGES" ]]; then
  BENCH_CMD+=("--languages" "$LANGUAGES")
fi
BENCH_CMD+=("--exercises-dir" "polyglot-benchmark")

docker "${DOCKER_ARGS[@]}" "$(printf '%q ' "${BENCH_CMD[@]}")"

RUN_DIR="$(ls -dt $RUN_DIR_GLOB 2>/dev/null | head -n 1 || true)"
if [[ -z "$RUN_DIR" || ! -d "$RUN_DIR" ]]; then
  echo "ERROR: benchmark run directory not found for tag $RUN_TAG" >&2
  exit 1
fi

python3 - "$RUN_DIR" "$RESULT_JSON" "$MODEL" "$OLLAMA_BASE" "${TASK_SUBSET:-}" "${KEYWORDS:-}" "${LANGUAGES:-}" <<'PY'
import json
import sys
from collections import defaultdict
from pathlib import Path

run_dir = Path(sys.argv[1])
result_json = Path(sys.argv[2])
model = sys.argv[3]
ollama_base = sys.argv[4]
task_subset = sys.argv[5] or None
keywords = sys.argv[6] or None
languages = sys.argv[7] or None

records = []
for path in sorted(run_dir.rglob(".aider.results.json")):
    if path.parent == run_dir:
        continue
    try:
        data = json.loads(path.read_text())
    except Exception as exc:
        records.append({
            "path": str(path.relative_to(run_dir)),
            "exception": f"parse_error: {exc}",
        })
        continue
    data["_path"] = str(path.relative_to(run_dir))
    records.append(data)

def truthy(x):
    return bool(x) and any(x)

lang_buckets = defaultdict(list)
for rec in records:
    if "_path" not in rec:
        continue
    lang = Path(rec["_path"]).parts[0] if Path(rec["_path"]).parts else "unknown"
    lang_buckets[lang].append(rec)

def summarize(items):
    done = len(items)
    if not done:
        return {
            "completed_tests": 0,
            "pass_rate_1": None,
            "pass_rate_2": None,
            "first_attempt_pass_rate": None,
            "eventual_pass_rate": None,
            "avg_runtime_seconds": None,
            "avg_prompt_tokens": None,
            "avg_completion_tokens": None,
            "avg_tokens_total": None,
        }
    pass1 = sum(1 for r in items if r.get("tests_outcomes", [False])[0])
    pass2 = sum(1 for r in items if truthy(r.get("tests_outcomes", [])))
    dur = sum(float(r.get("duration", 0.0)) for r in items)
    prompt = sum(float(r.get("prompt_tokens", 0.0)) for r in items)
    completion = sum(float(r.get("completion_tokens", 0.0)) for r in items)
    return {
        "completed_tests": done,
        "pass_rate_1": round(100 * pass1 / done, 1),
        "pass_rate_2": round(100 * pass2 / done, 1),
        "first_attempt_pass_rate": round(100 * pass1 / done, 1),
        "eventual_pass_rate": round(100 * pass2 / done, 1),
        "avg_runtime_seconds": round(dur / done, 2),
        "avg_prompt_tokens": round(prompt / done, 1),
        "avg_completion_tokens": round(completion / done, 1),
        "avg_tokens_total": round((prompt + completion) / done, 1),
    }

summary = summarize([r for r in records if "_path" in r])
language_breakdown = {}
for lang, items in sorted(lang_buckets.items()):
    language_breakdown[lang] = summarize(items)

payload = {
    "model": model,
    "ollama_api_base": ollama_base,
    "run_dir": str(run_dir),
    "task_count": summary["completed_tests"],
    "task_subset": int(task_subset) if task_subset else None,
    "keywords": keywords,
    "languages": languages,
    "summary": summary,
    "language_breakdown": language_breakdown,
    "records": [
        {k: v for k, v in rec.items() if k != "_path"}
        for rec in records
    ],
}
result_json.write_text(json.dumps(payload, indent=2, sort_keys=True))
print(result_json)
PY

echo "$RESULT_JSON"
