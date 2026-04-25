#!/usr/bin/env python3
"""Collect real training examples from executor history.

Usage:
    python3 bin/collect_training_data.py              # dry-run: show stats
    python3 bin/collect_training_data.py --write      # write to artifacts/training_data/
    python3 bin/collect_training_data.py --write --format chatml

Output (--write):
    artifacts/training_data/alpaca.jsonl    (default)
    artifacts/training_data/chatml.jsonl    (--format chatml)
    artifacts/training_data/summary.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.training_data_collector import (
    collect,
    write_alpaca_jsonl,
    write_chatml_jsonl,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect training data from executor artifacts")
    parser.add_argument("--write", action="store_true", help="Write JSONL output files")
    parser.add_argument("--format", choices=["alpaca", "chatml", "both"], default="both")
    parser.add_argument("--min-diff-lines", type=int, default=3)
    parser.add_argument("--out-dir", default=str(REPO_ROOT / "artifacts" / "training_data"))
    args = parser.parse_args()

    out_dir = Path(args.out_dir)

    print("Scanning execution artifacts...")
    examples = list(collect(min_diff_lines=args.min_diff_lines))

    if not examples:
        print("No valid training examples found.")
        print()
        print("Why: Before commit 4ec96e3 (2026-04-24), the executor used --no-auto-commits")
        print("and reported the pre-run HEAD as commit_hash, so old 'success' artifacts have")
        print("no real .py diffs. Examples accumulate as the fixed executor runs real tasks.")
        print()
        print("To generate training data: run the executor on a few items, then re-run this script.")
        return 0

    # Stats
    print(f"\n{'='*60}")
    print(f"Found {len(examples)} real training examples")
    print(f"{'='*60}")

    from collections import Counter
    models = Counter(ex.meta["model"] for ex in examples)
    sizes = sorted(ex.meta["diff_lines_added"] for ex in examples)

    print(f"\nBy model:")
    for model, count in models.most_common():
        print(f"  {model}: {count}")

    print(f"\nDiff size distribution (lines added):")
    print(f"  min={sizes[0]}, median={sizes[len(sizes)//2]}, max={sizes[-1]}")

    print(f"\nSample instructions:")
    for ex in examples[:5]:
        print(f"  [{ex.meta['commit']}] {ex.instruction[:80]!r}")

    summary = {
        "total": len(examples),
        "by_model": dict(models),
        "diff_size_min": sizes[0],
        "diff_size_median": sizes[len(sizes)//2],
        "diff_size_max": sizes[-1],
        "sft_ready": len(examples) >= 10,
        "lora_ready": len(examples) >= 50,
        "note": "lora_ready threshold is approximate; quality matters more than quantity",
    }

    if args.write:
        print(f"\nWriting to {out_dir}/")
        out_dir.mkdir(parents=True, exist_ok=True)

        if args.format in ("alpaca", "both"):
            n = write_alpaca_jsonl(examples, out_dir / "alpaca.jsonl")
            print(f"  alpaca.jsonl: {n} examples")

        if args.format in ("chatml", "both"):
            n = write_chatml_jsonl(examples, out_dir / "chatml.jsonl")
            print(f"  chatml.jsonl: {n} examples")

        (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
        print(f"  summary.json: written")

        print(f"\nNext step:")
        if not summary["sft_ready"]:
            print(f"  Need {10 - len(examples)} more examples before SFT training is viable.")
            print(f"  Run the executor on more tasks, then re-collect.")
        elif not summary["lora_ready"]:
            print(f"  Have enough for a quick SFT run. For stable LoRA, need {50 - len(examples)} more.")
            print(f"  Install deps and train:")
            print(f"    pip install torch transformers peft datasets accelerate bitsandbytes")
            print(f"    python3 bin/run_training_cycle.py --data {out_dir}/alpaca.jsonl")
        else:
            print(f"  Ready for LoRA fine-tuning:")
            print(f"    pip install torch transformers peft datasets accelerate bitsandbytes")
            print(f"    python3 bin/run_training_cycle.py --data {out_dir}/alpaca.jsonl")
    else:
        print(f"\nRe-run with --write to save JSONL files.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
