#!/usr/bin/env python3
"""D-17-91 benchmark harness — qwen3-coder-next vs T3-B (qwen3-coder:30b) comparison.

Adapted from D-17-12 bench.py. Scope: T3-B (existing baseline) + T3-C (qwen3-coder-next
on Mac Studio). Gemma 4 deferred — not in Ollama registry as of 2026-05-04.

Runs (model x workload) pairs against Ollama daemons and writes
per-pair JSON result records.

Workloads:
  - long-context: 16K+ token analysis tasks
  - refactor: multi-file code refactor
  - tool-call: stream:false tool-call adherence (model-competence
    in isolation; agent-integration deferred)
  - agentic: multi-step autonomous task with verify loops

Models defined in MODELS dict. Tasks loaded from task-sets/*.json.

Output: results/<run-id>/<model>__<workload>.json
        results/<run-id>/summary.json

Usage:
  python3 bench.py [--models M1,M2,...] [--workloads W1,W2,...]
                   [--task-set-dir DIR] [--out-dir DIR]
                   [--samples N] [--dry-run]

Conventions:
- Direct Ollama API (/api/chat) with stream=false to avoid the
  Finding 1+2 streaming/tool-call gaps
- Records: ttft_s, total_s, eval_count, eval_duration_ns,
  load_duration_ns, prompt_eval_count, prompt_eval_duration_ns,
  peak_runner_rss_bytes (sampled)
- Quality scoring: per-workload check function -> {pass: bool,
  score: float [0,1], notes: str}
- Auto-grading is initial; WP-06 surface-back for hand-grading
  guidance.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import request as urlreq

REPO_ROOT = Path(__file__).resolve().parents[3]
HARNESS_DIR = Path(__file__).resolve().parent
DEFAULT_TASKSET_DIR = HARNESS_DIR.parent / "task-sets"
DEFAULT_OUT_DIR = HARNESS_DIR.parent / "results"

MODELS = {
    "T3-B": {
        "name": "qwen3-coder:30b",
        "host": "192.168.10.142",
        "port": 11434,
        "host_label": "mac-studio",
        "tier": "T3-B",
        "context_limit": 262144,
        "ssh_target": "admin@192.168.10.142",
    },
    "T3-C": {
        # qwen3-coder-next: 79.7B qwen3next MoE, Q4_K_M, 51 GB on disk.
        # 512 experts, 10 active (expert_used_count=10). tools supported.
        # Pulled 2026-05-04 on Mac Studio (96 GB unified pool).
        # Verified: context_length=262144 (ollama show --verbose 2026-05-04).
        "name": "qwen3-coder-next",
        "host": "192.168.10.142",
        "port": 11434,
        "host_label": "mac-studio",
        "tier": "T3-C",
        "context_limit": 262144,
        "ssh_target": "admin@192.168.10.142",
    },
}

WORKLOADS = ["long-context", "refactor", "tool-call", "agentic"]


def http_post(url, body, timeout=900):
    """POST JSON to Ollama, parse JSON response. Returns (response_dict, wall_seconds)."""
    data = json.dumps(body).encode("utf-8")
    req = urlreq.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.monotonic()
    with urlreq.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    wall = time.monotonic() - t0
    return json.loads(raw.decode("utf-8")), wall


def measure_runner_rss(model_cfg):
    """Sample peak RSS of the ollama runner subprocess for this model.

    Ollama runners are spawned per-model as subprocesses. We sample
    the runner's RSS via ps over SSH (Studio) or directly (Mini).
    """
    model_name = model_cfg["name"]
    if model_cfg["ssh_target"]:
        cmd = [
            "ssh",
            "-o",
            "ConnectTimeout=4",
            model_cfg["ssh_target"],
            "ps -axo rss,command | grep ollama | grep -E 'runner|model' | grep -v grep | awk '{print $1}' | sort -n | tail -1",
        ]
    else:
        cmd = [
            "sh",
            "-c",
            "ps -axo rss,command | grep ollama | grep -E 'runner|model' | grep -v grep | awk '{print $1}' | sort -n | tail -1",
        ]
    try:
        out = subprocess.run(
            cmd, capture_output=True, text=True, timeout=10
        )
        rss_kb = int(out.stdout.strip() or "0")
        return rss_kb * 1024
    except Exception:
        return 0


def warmup(model_cfg):
    """Force the model into memory with a 1-token completion."""
    url = f"http://{model_cfg['host']}:{model_cfg['port']}/api/chat"
    body = {
        "model": model_cfg["name"],
        "messages": [{"role": "user", "content": "Hi."}],
        "stream": False,
        "options": {"num_predict": 1},
    }
    try:
        http_post(url, body, timeout=300)
    except Exception as e:
        print(f"  WARMUP FAILED for {model_cfg['name']}: {e}", file=sys.stderr)


def run_one(model_key, model_cfg, workload, task_set, samples_cap):
    """Run all sample tasks for (model, workload). Return result dict."""
    url = f"http://{model_cfg['host']}:{model_cfg['port']}/api/chat"
    tasks = task_set[:samples_cap]

    samples = []
    print(f"  warming up {model_cfg['name']}...")
    warmup(model_cfg)

    for i, task in enumerate(tasks):
        sample = {
            "task_id": task["id"],
            "task_summary": task.get("summary", task["id"]),
        }

        # Skip-or-truncate guard for context-window mismatches
        prompt_tokens_est = task.get("approx_input_tokens", 0)
        if prompt_tokens_est >= model_cfg["context_limit"]:
            sample["status"] = "n/a-context-insufficient"
            sample["reason"] = (
                f"task input ~{prompt_tokens_est} tok exceeds model context limit "
                f"{model_cfg['context_limit']} — recorded as N/A to preserve "
                f"comparison fairness (no artificial truncation)"
            )
            samples.append(sample)
            continue

        body = {
            "model": model_cfg["name"],
            "messages": task["messages"],
            "stream": False,
            "options": task.get("options", {"temperature": 0.1, "num_predict": 1024}),
        }
        if task.get("tools"):
            body["tools"] = task["tools"]
        if task.get("format"):
            body["format"] = task["format"]

        t0 = time.monotonic()
        try:
            resp, wall = http_post(url, body, timeout=task.get("timeout", 900))
        except Exception as e:
            sample["status"] = "error"
            sample["error"] = str(e)
            sample["wall_s"] = time.monotonic() - t0
            samples.append(sample)
            continue

        sample["status"] = "ok"
        sample["wall_s"] = wall
        # Ollama returns ns durations
        for k in (
            "total_duration",
            "load_duration",
            "prompt_eval_count",
            "prompt_eval_duration",
            "eval_count",
            "eval_duration",
        ):
            if k in resp:
                sample[k] = resp[k]
        if "eval_count" in resp and "eval_duration" in resp and resp["eval_duration"] > 0:
            sample["tokens_per_sec"] = resp["eval_count"] / (resp["eval_duration"] / 1e9)
        msg = resp.get("message", {})
        sample["response_role"] = msg.get("role", "")
        sample["response_content"] = msg.get("content", "")
        sample["tool_calls"] = msg.get("tool_calls", [])
        sample["finish_reason"] = resp.get("done_reason", "")

        # Quality grading
        try:
            grade = grade_sample(workload, task, sample)
        except Exception as e:
            grade = {"pass": False, "score": 0.0, "notes": f"grader error: {e}"}
        sample["grade"] = grade

        samples.append(sample)
        score_str = f"{grade['score']:.2f}" if grade.get("score") is not None else "n/a"
        print(
            f"    [{i+1}/{len(tasks)}] {task['id']}: "
            f"wall={wall:.1f}s tps={sample.get('tokens_per_sec',0):.1f} "
            f"grade={score_str} pass={grade.get('pass')}"
        )

    peak_rss = measure_runner_rss(model_cfg)

    return {
        "model_key": model_key,
        "model_name": model_cfg["name"],
        "model_tier": model_cfg["tier"],
        "model_host": model_cfg["host_label"],
        "context_limit": model_cfg["context_limit"],
        "workload": workload,
        "samples": samples,
        "peak_runner_rss_bytes": peak_rss,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "n_samples_attempted": len(tasks),
        "n_samples_ok": sum(1 for s in samples if s["status"] == "ok"),
        "n_samples_skipped": sum(
            1 for s in samples if s["status"] == "n/a-context-insufficient"
        ),
        "n_samples_error": sum(1 for s in samples if s["status"] == "error"),
    }


# ---------- Quality graders (per-workload) ----------

def grade_sample(workload, task, sample):
    if sample["status"] != "ok":
        return {"pass": False, "score": 0.0, "notes": f"sample {sample['status']}"}
    if workload == "long-context":
        return grade_long_context(task, sample)
    if workload == "refactor":
        return grade_refactor(task, sample)
    if workload == "tool-call":
        return grade_tool_call(task, sample)
    if workload == "agentic":
        return grade_agentic(task, sample)
    return {"pass": False, "score": 0.0, "notes": f"unknown workload {workload}"}


def grade_long_context(task, sample):
    """Long-context tasks have an `expected_facts` array of strings
    that should appear in the response (case-insensitive)."""
    content = (sample["response_content"] or "").lower()
    expected = task.get("expected_facts", [])
    if not expected:
        return {"pass": False, "score": 0.0, "notes": "no expected_facts"}
    hits = sum(1 for f in expected if f.lower() in content)
    score = hits / len(expected)
    return {
        "pass": score >= 0.7,
        "score": score,
        "notes": f"{hits}/{len(expected)} expected facts present",
    }


def grade_refactor(task, sample):
    """Refactor tasks check for required transformations in the
    output. `must_contain` (all must appear) + `must_not_contain`
    (none may appear)."""
    content = sample["response_content"] or ""
    must = task.get("must_contain", [])
    must_not = task.get("must_not_contain", [])
    hits = sum(1 for s in must if s in content)
    bad = sum(1 for s in must_not if s in content)
    if not must:
        return {"pass": False, "score": 0.0, "notes": "no must_contain"}
    score = hits / len(must)
    if bad > 0:
        score = max(0.0, score - 0.5 * bad / max(1, len(must_not)))
    return {
        "pass": score >= 0.7 and bad == 0,
        "score": score,
        "notes": f"{hits}/{len(must)} required transforms; {bad} forbidden",
    }


def _try_parse_inline_tool_call(content):
    """Try to parse JSON-in-content tool-call emission patterns:
    - bare JSON object  {"name": "...", "arguments": {...}}
    - <tools>...</tools> envelope (Qwen native)
    - fenced ```json ... ```
    Returns dict {name: str, arguments: dict} or None.
    """
    if not content:
        return None
    # Strip fenced code blocks
    candidates = [content]
    fence = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
    candidates.extend(fence)
    # Strip <tools>...</tools>
    tools_env = re.findall(r"<tools>\s*(\{.*?\})\s*</tools>", content, re.DOTALL)
    candidates.extend(tools_env)
    # Greedy: largest balanced-{} substring
    for c in candidates:
        c = c.strip()
        if not c.startswith("{"):
            # find first { and try
            idx = c.find("{")
            if idx < 0:
                continue
            c = c[idx:]
        try:
            obj = json.loads(c)
        except Exception:
            continue
        # Common shapes
        if "name" in obj and "arguments" in obj:
            args = obj["arguments"]
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    pass
            return {"name": obj["name"], "arguments": args}
        if "function" in obj and isinstance(obj["function"], dict):
            f = obj["function"]
            args = f.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    pass
            return {"name": f.get("name", ""), "arguments": args}
    return None


def grade_tool_call(task, sample):
    """Tool-call tasks expect either a structured tool_calls array OR
    a JSON-in-content emission. Records both modes; partial credit when
    serving stack drops the structured envelope (Finding 1+2 territory).
    """
    tcs = sample.get("tool_calls", [])
    expected_fn = task.get("expected_function")
    expected_args = task.get("expected_args", {})

    # Special case: expected_function == None means "no tool needed"
    if expected_fn is None:
        if tcs or _try_parse_inline_tool_call(sample.get("response_content", "")):
            return {
                "pass": False,
                "score": 0.0,
                "notes": "called a tool when none was needed",
            }
        return {
            "pass": True,
            "score": 1.0,
            "notes": "correctly answered without tool call",
        }

    structured = bool(tcs)
    fn_name = ""
    args = {}
    if structured:
        tc = tcs[0]
        fn_name = tc.get("function", {}).get("name", "")
        args = tc.get("function", {}).get("arguments", {})
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                args = {}
    else:
        inline = _try_parse_inline_tool_call(sample.get("response_content", ""))
        if inline:
            fn_name = inline["name"]
            args = inline["arguments"] or {}

    if not fn_name:
        return {"pass": False, "score": 0.0, "notes": "no tool call detected"}
    if fn_name != expected_fn:
        return {
            "pass": False,
            "score": 0.3,
            "notes": f"called wrong function: {fn_name} (expected {expected_fn})",
        }
    arg_hits = sum(
        1
        for k, v in expected_args.items()
        if str(args.get(k, "")).lower() == str(v).lower()
    )
    # Base score depends on emission mode
    base = 0.6 if structured else 0.45  # structured emission is the spec
    score = base + (1.0 - base) * arg_hits / max(1, len(expected_args))
    return {
        "pass": arg_hits == len(expected_args) and structured,
        "score": score,
        "notes": (
            f"called {fn_name} ({'structured' if structured else 'inline JSON'}); "
            f"{arg_hits}/{len(expected_args)} args match"
        ),
    }


def grade_agentic(task, sample):
    """Agentic tasks check for a structured plan + execution markers
    in the output. `expected_steps` = ordered list of step keywords."""
    content = (sample["response_content"] or "").lower()
    steps = task.get("expected_steps", [])
    if not steps:
        return {"pass": False, "score": 0.0, "notes": "no expected_steps"}
    pos = -1
    in_order = 0
    hits = 0
    for s in steps:
        idx = content.find(s.lower(), pos + 1)
        if idx >= 0:
            hits += 1
            if idx > pos:
                in_order += 1
                pos = idx
    score = 0.5 * (hits / len(steps)) + 0.5 * (in_order / len(steps))
    return {
        "pass": score >= 0.7,
        "score": score,
        "notes": f"{hits}/{len(steps)} steps present, {in_order} in order",
    }


# ---------- Driver ----------

def load_taskset(taskset_dir, workload):
    p = taskset_dir / f"{workload}.json"
    if not p.exists():
        raise FileNotFoundError(f"task set missing: {p}")
    with open(p) as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default=",".join(MODELS.keys()))
    ap.add_argument("--workloads", default=",".join(WORKLOADS))
    ap.add_argument("--task-set-dir", default=str(DEFAULT_TASKSET_DIR))
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    ap.add_argument("--samples", type=int, default=4, help="cap samples per workload")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    model_keys = [m.strip() for m in args.models.split(",") if m.strip()]
    workloads = [w.strip() for w in args.workloads.split(",") if w.strip()]
    taskset_dir = Path(args.task_set_dir)
    out_dir = Path(args.out_dir)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = out_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "run_id": run_id,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "models": [{"key": k, **MODELS[k]} for k in model_keys],
        "workloads": workloads,
        "samples_cap": args.samples,
        "results": [],
    }

    print(f"=== D-17-91 bench run {run_id} (T3-B vs T3-C) ===")
    for workload in workloads:
        try:
            tasks = load_taskset(taskset_dir, workload)
        except FileNotFoundError as e:
            print(f"  SKIP workload {workload}: {e}")
            continue
        for mk in model_keys:
            mc = MODELS[mk]
            print(f"\n[{mk} {mc['name']} on {mc['host_label']}] workload={workload}")
            if args.dry_run:
                print("  (dry-run)")
                continue
            res = run_one(mk, mc, workload, tasks, args.samples)
            outp = run_dir / f"{mk}__{workload}.json"
            with open(outp, "w") as f:
                json.dump(res, f, indent=2)
            summary["results"].append(
                {
                    "model_key": mk,
                    "workload": workload,
                    "n_ok": res["n_samples_ok"],
                    "n_skipped": res["n_samples_skipped"],
                    "n_error": res["n_samples_error"],
                    "mean_score": (
                        sum(s["grade"]["score"] for s in res["samples"] if s["status"] == "ok")
                        / max(1, res["n_samples_ok"])
                    ),
                    "mean_tps": (
                        sum(s.get("tokens_per_sec", 0) for s in res["samples"] if s["status"] == "ok")
                        / max(1, res["n_samples_ok"])
                    ),
                    "peak_rss_gb": res["peak_runner_rss_bytes"] / 1e9,
                }
            )

    summary["finished_utc"] = datetime.now(timezone.utc).isoformat()
    with open(run_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n=== summary written: {run_dir / 'summary.json'} ===")


if __name__ == "__main__":
    main()
