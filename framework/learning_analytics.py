"""Analyze executor performance and training data readiness.

Usage:
    python3 -m framework.learning_analytics          # full report
    python3 -m framework.learning_analytics --json   # machine-readable
    python3 -m framework.learning_analytics --since 2026-04-20  # filter by date
"""
from __future__ import annotations

import json
import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

REPO_ROOT = Path(__file__).parent.parent
ARTIFACTS = REPO_ROOT / "artifacts"
TRAINING_THRESHOLDS = {"sft": 10, "lora": 50, "stable": 200}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _load_executions(since: datetime | None = None) -> list[dict]:
    executions_dir = ARTIFACTS / "executions"
    if not executions_dir.exists():
        return []
    results = []
    for p in sorted(executions_dir.glob("*.json")):
        try:
            d = json.loads(p.read_text())
            d["_file"] = p.name
            # Parse timestamp from filename: YYYYMMDD_HHMMSS_...
            m = re.match(r"(\d{8}_\d{6})", p.name)
            if m:
                d["_ts"] = datetime.strptime(m.group(1), "%Y%m%d_%H%M%S")
            else:
                d["_ts"] = None
            if since and d["_ts"] and d["_ts"] < since:
                continue
            results.append(d)
        except (OSError, json.JSONDecodeError):
            pass
    return results


def _load_metrics(since: datetime | None = None) -> list[dict]:
    metrics_path = ARTIFACTS / "execution_metrics.jsonl"
    if not metrics_path.exists():
        return []
    results = []
    for line in metrics_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            ts_str = d.get("timestamp", "")
            try:
                d["_ts"] = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                d["_ts"] = None
            if since and d["_ts"] and d["_ts"].replace(tzinfo=None) < since:
                continue
            results.append(d)
        except json.JSONDecodeError:
            pass
    return results


def _load_training_examples() -> list[dict]:
    alpaca_path = ARTIFACTS / "training_data" / "alpaca.jsonl"
    if not alpaca_path.exists():
        return []
    examples = []
    for line in alpaca_path.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                examples.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return examples


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

@dataclass
class ExecutionStats:
    total: int = 0
    succeeded: int = 0
    failed: int = 0
    by_model: dict = field(default_factory=dict)
    by_failure_type: dict = field(default_factory=dict)
    success_rate: float = 0.0
    real_commits: int = 0  # successes with HEAD advancing
    avg_duration_s: float | None = None
    recent_trend: str = "unknown"  # "improving", "stable", "degrading"


def analyze_executions(execs: list[dict]) -> ExecutionStats:
    if not execs:
        return ExecutionStats()

    stats = ExecutionStats(total=len(execs))
    model_success: dict[str, list[bool]] = defaultdict(list)
    durations: list[float] = []

    for d in execs:
        success = bool(d.get("success"))
        model = d.get("model", d.get("model_used", "unknown"))
        model_success[model].append(success)

        if success:
            stats.succeeded += 1
            commit = d.get("commit_hash", "")
            if commit and len(commit) >= 8:
                stats.real_commits += 1
        else:
            stats.failed += 1
            sigs = d.get("failure_signatures", [])
            if isinstance(sigs, list) and sigs:
                for sig in sigs[:1]:
                    key = sig.get("type", "unknown") if isinstance(sig, dict) else str(sig)
                    stats.by_failure_type[key] = stats.by_failure_type.get(key, 0) + 1
            else:
                err = d.get("error", "")
                key = "timeout" if "timeout" in str(err).lower() else "other"
                stats.by_failure_type[key] = stats.by_failure_type.get(key, 0) + 1

    stats.success_rate = stats.succeeded / stats.total if stats.total else 0.0
    stats.by_model = {
        m: {"total": len(v), "success": sum(v), "rate": sum(v) / len(v) if v else 0}
        for m, v in model_success.items()
    }

    # Trend: compare last 20% vs first 20% success rate
    if stats.total >= 10:
        chunk = max(1, stats.total // 5)
        early = [d.get("success") for d in execs[:chunk]]
        recent = [d.get("success") for d in execs[-chunk:]]
        early_rate = sum(early) / len(early) if early else 0
        recent_rate = sum(recent) / len(recent) if recent else 0
        if recent_rate - early_rate > 0.1:
            stats.recent_trend = "improving"
        elif early_rate - recent_rate > 0.1:
            stats.recent_trend = "degrading"
        else:
            stats.recent_trend = "stable"

    return stats


@dataclass
class TrainingReadiness:
    example_count: int = 0
    sft_ready: bool = False
    lora_ready: bool = False
    stable_ready: bool = False
    needed_for_lora: int = 0
    needed_for_stable: int = 0
    instructions_sample: list[str] = field(default_factory=list)
    diff_size_median: int = 0
    diff_size_max: int = 0


def _is_quality_example(ex: dict) -> bool:
    """True if example is a clean code addition, not a whole-file rewrite or README-contaminated."""
    output = ex.get("output", "")
    added = sum(1 for l in output.splitlines() if l.startswith("+") and not l.startswith("+++"))
    # Exclude huge diffs (>200 added lines = likely whole-file rewrite of large file)
    if added > 200:
        return False
    # Exclude examples where README.md appeared in the instruction (fallback contamination)
    instruction = ex.get("instruction", "")
    if "README.md" in instruction:
        return False
    return True


def analyze_training_data() -> TrainingReadiness:
    examples = _load_training_examples()
    quality = [e for e in examples if _is_quality_example(e)]
    n = len(examples)
    nq = len(quality)
    r = TrainingReadiness(
        example_count=nq,  # report quality count as the usable number
        sft_ready=nq >= TRAINING_THRESHOLDS["sft"],
        lora_ready=nq >= TRAINING_THRESHOLDS["lora"],
        stable_ready=nq >= TRAINING_THRESHOLDS["stable"],
        needed_for_lora=max(0, TRAINING_THRESHOLDS["lora"] - nq),
        needed_for_stable=max(0, TRAINING_THRESHOLDS["stable"] - nq),
    )
    if examples:
        r.instructions_sample = [ex["instruction"][:80] for ex in quality[-3:]] or [ex["instruction"][:80] for ex in examples[-3:]]
        all_sizes = sorted(
            sum(1 for l in ex.get("output", "").splitlines() if l.startswith("+") and not l.startswith("+++"))
            for ex in examples
        )
        quality_sizes = sorted(
            sum(1 for l in ex.get("output", "").splitlines() if l.startswith("+") and not l.startswith("+++"))
            for ex in quality
        ) if quality else all_sizes
        r.diff_size_median = quality_sizes[len(quality_sizes) // 2] if quality_sizes else 0
        r.diff_size_max = quality_sizes[-1] if quality_sizes else 0
        # Store raw count for display
        r._raw_count = n  # type: ignore[attr-defined]
        r._filtered = n - nq  # type: ignore[attr-defined]
    return r


@dataclass
class LearningReport:
    generated_at: str = ""
    execution_stats: ExecutionStats = field(default_factory=ExecutionStats)
    training: TrainingReadiness = field(default_factory=TrainingReadiness)
    recommendation: str = ""
    next_steps: list[str] = field(default_factory=list)


def build_report(since: datetime | None = None) -> LearningReport:
    execs = _load_executions(since)
    stats = analyze_executions(execs)
    training = analyze_training_data()

    report = LearningReport(
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        execution_stats=stats,
        training=training,
    )

    # Recommendation logic
    if not training.sft_ready:
        need = TRAINING_THRESHOLDS["sft"] - training.example_count
        report.recommendation = f"Need {need} more successful commits to reach SFT threshold."
        report.next_steps = [
            f"Run: python3 bin/auto_execute_roadmap.py --max-items 10",
            "Each successful commit with ≥3 py lines added counts as one training example.",
        ]
    elif not training.lora_ready:
        need = training.needed_for_lora
        report.recommendation = f"SFT-ready ({training.example_count} examples). Need {need} more for stable LoRA."
        report.next_steps = [
            f"Run: python3 bin/run_training_cycle.py --collect-only  # verify count",
            f"Run: python3 bin/run_training_cycle.py  # SFT training is viable now",
            f"Continue: python3 bin/auto_execute_roadmap.py --max-items 20  # grow toward LoRA",
        ]
    else:
        report.recommendation = f"LoRA-ready! {training.example_count} examples available."
        report.next_steps = [
            "Run: python3 bin/run_training_cycle.py  # full LoRA fine-tuning",
            "After training: python3 bin/run_training_cycle.py --export-gguf --adapter artifacts/lora_adapter/adapter",
        ]

    if stats.recent_trend == "degrading":
        report.next_steps.insert(0, "⚠️  Success rate degrading recently — check aider model and Ollama load.")

    return report


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_report(report: LearningReport) -> None:
    s = report.execution_stats
    t = report.training

    print(f"\n{'='*60}")
    print(f"  Learning Analytics  —  {report.generated_at}")
    print(f"{'='*60}")

    print(f"\n── Execution History ({s.total} total) ──")
    print(f"  Success rate : {s.success_rate:.0%}  ({s.succeeded}/{s.total})")
    print(f"  Real commits : {s.real_commits}")
    print(f"  Trend        : {s.recent_trend}")

    if s.by_model:
        print(f"\n── By Model ──")
        for model, m in sorted(s.by_model.items(), key=lambda kv: -kv[1]["total"]):
            print(f"  {model:<30} {m['success']}/{m['total']}  ({m['rate']:.0%})")

    if s.by_failure_type:
        print(f"\n── Failure Breakdown ──")
        for ftype, count in sorted(s.by_failure_type.items(), key=lambda kv: -kv[1]):
            print(f"  {ftype:<20} {count}")

    sft_need = TRAINING_THRESHOLDS["sft"] - t.example_count
    sft_str = "✓" if t.sft_ready else f"✗  (need {sft_need} more)"
    lora_str = "✓" if t.lora_ready else f"✗  (need {t.needed_for_lora} more)"
    stable_str = "✓" if t.stable_ready else f"✗  (need {t.needed_for_stable} more)"

    raw = getattr(t, "_raw_count", t.example_count)
    filtered = getattr(t, "_filtered", 0)

    print(f"\n── Training Data ──")
    quality_note = f"  ({filtered} discarded: README fallback or >200-line rewrites)" if filtered else ""
    print(f"  Quality examples : {t.example_count}{quality_note}")
    if raw != t.example_count:
        print(f"  Raw collected    : {raw}  (run --collect-only to update)")
    print(f"  SFT-ready   : {sft_str}")
    print(f"  LoRA-ready  : {lora_str}")
    print(f"  Stable-ready: {stable_str}")
    if t.diff_size_median:
        print(f"  Diff median : {t.diff_size_median} lines  (max {t.diff_size_max})")
    if t.instructions_sample:
        print(f"  Recent examples:")
        for inst in t.instructions_sample:
            print(f"    · {inst}")

    print(f"\n── Recommendation ──")
    print(f"  {report.recommendation}")
    if report.next_steps:
        print(f"\n── Next Steps ──")
        for step in report.next_steps:
            print(f"  {step}")
    print()


def to_dict(report: LearningReport) -> dict:
    import dataclasses
    return dataclasses.asdict(report)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Executor learning analytics report")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--since", help="Filter to executions after date (YYYY-MM-DD)")
    args = parser.parse_args()

    since = None
    if args.since:
        try:
            since = datetime.strptime(args.since, "%Y-%m-%d")
        except ValueError:
            print(f"Invalid date: {args.since}  (expected YYYY-MM-DD)")
            return 1

    report = build_report(since=since)

    if args.json:
        print(json.dumps(to_dict(report), indent=2, default=str))
    else:
        print_report(report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
