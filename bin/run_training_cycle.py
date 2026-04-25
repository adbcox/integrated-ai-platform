#!/usr/bin/env python3
"""End-to-end training cycle: collect → format → train → evaluate.

ISOLATION: Training deps (torch, transformers, peft) live in ~/training-env,
isolated from aider's uv environment. This script auto-detects and uses the
venv; it creates the venv and installs deps if they're missing.

Aider runs via uv (/Users/admin/.local/share/uv/tools/aider-chat/). The
system Python 3.9 (pip3) is NOT used for training — never install training
libs there.

The base model (Qwen2.5-Coder-7B-Instruct) is downloaded from HuggingFace
on first run (~14 GB). Set HF_HOME to control cache location.

Usage:
    # Full cycle (collect + train + eval)
    python3 bin/run_training_cycle.py

    # Collect only — works without any ML deps
    python3 bin/run_training_cycle.py --collect-only

    # Use pre-collected data
    python3 bin/run_training_cycle.py --data artifacts/training_data/alpaca.jsonl

    # Train only
    python3 bin/run_training_cycle.py --train-only --data artifacts/training_data/alpaca.jsonl

    # Export to GGUF for Ollama (requires llama.cpp)
    python3 bin/run_training_cycle.py --export-gguf --adapter artifacts/lora_adapter/adapter

    # Activate venv manually for debugging:
    source ~/training-env/bin/activate
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
VENV_DIR = Path.home() / "training-env"
VENV_PYTHON = VENV_DIR / "bin" / "python"
TRAINING_DEPS = ["torch", "transformers", "peft", "datasets", "accelerate"]

sys.path.insert(0, str(REPO_ROOT))


def _ensure_venv() -> bool:
    """Create ~/training-env if missing and install training deps."""
    if not VENV_DIR.exists():
        print(f"Creating isolated training venv at {VENV_DIR} ...")
        # Use Python 3.12 from brew for best torch/MPS compatibility
        python_bin = "/opt/homebrew/bin/python3.12"
        if not Path(python_bin).exists():
            python_bin = sys.executable  # fallback to current interpreter
        result = subprocess.run([python_bin, "-m", "venv", str(VENV_DIR)])
        if result.returncode != 0:
            print(f"Failed to create venv. Try: {python_bin} -m venv ~/training-env")
            return False
        print(f"Venv created with {python_bin}")

    # Check which deps are missing inside the venv
    missing = []
    for pkg in TRAINING_DEPS:
        check = subprocess.run(
            [str(VENV_PYTHON), "-c", f"import {pkg.replace('-', '_')}"],
            capture_output=True,
        )
        if check.returncode != 0:
            missing.append(pkg)

    if missing:
        print(f"Installing into venv: {', '.join(missing)}")
        print("(torch is ~2 GB — first install takes a few minutes)")
        result = subprocess.run(
            [str(VENV_DIR / "bin" / "pip"), "install", "--quiet", *missing]
        )
        if result.returncode != 0:
            print("Install failed. Check network / disk space.")
            return False
        print("Done installing.")

    return True


def _relaunch_in_venv() -> None:
    """If not already running in the training venv, re-exec inside it."""
    if sys.executable == str(VENV_PYTHON):
        return  # already in venv
    if not VENV_PYTHON.exists():
        return  # venv not created yet — let _ensure_venv handle it
    # Re-execute this script under the venv's Python
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON)] + sys.argv)


def _check_training_deps() -> bool:
    """Check training deps are available in the current interpreter."""
    missing = []
    for pkg in ("torch", "transformers", "peft", "datasets"):
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"Missing in current env: {', '.join(missing)}")
        print(f"Run: {VENV_PYTHON} {' '.join(sys.argv)}")
        return False
    return True


def _collect(out_dir: Path, fmt: str) -> Path | None:
    from framework.training_data_collector import collect, write_alpaca_jsonl, write_chatml_jsonl

    print("Collecting training examples from executor artifacts...")
    examples = list(collect())

    if not examples:
        print("No valid training examples found yet.")
        print("The executor must run real tasks (after commit 4ec96e3) to accumulate data.")
        print("Run: python3 bin/auto_execute_roadmap.py --max-items 10")
        print("Then re-run this script.")
        return None

    print(f"Found {len(examples)} examples.")
    out_dir.mkdir(parents=True, exist_ok=True)

    alpaca_path = out_dir / "alpaca.jsonl"
    write_alpaca_jsonl(examples, alpaca_path)
    write_chatml_jsonl(examples, out_dir / "chatml.jsonl")

    summary = {
        "total": len(examples),
        "sft_ready": len(examples) >= 10,
        "lora_ready": len(examples) >= 50,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"Wrote {len(examples)} examples to {out_dir}/")
    return alpaca_path


def _train(data_path: Path) -> Path | None:
    from framework.model_trainer import TrainingConfig, train

    print(f"\nStarting LoRA fine-tuning from {data_path}")
    print("This downloads ~14 GB on first run and takes 30-120 min on Apple Silicon.")

    config = TrainingConfig()
    try:
        adapter_path = train(data_path, config)
        print(f"\nAdapter saved: {adapter_path}")
        return adapter_path
    except RuntimeError as e:
        print(f"Training failed: {e}")
        return None


def _evaluate(adapter_path: Path, data_path: Path) -> None:
    from framework.model_trainer import evaluate_on_tasks

    import json
    records = [json.loads(l) for l in data_path.read_text().splitlines() if l.strip()]
    # Hold out last 10% as eval set
    split = max(1, int(len(records) * 0.9))
    eval_tasks = records[split:]

    if not eval_tasks:
        print("No eval examples (need >10 total training examples).")
        return

    print(f"\nEvaluating on {len(eval_tasks)} held-out tasks...")
    results = evaluate_on_tasks(adapter_path, eval_tasks)
    print(f"Pass rate: {results['pass_rate']:.0%} ({results['pass']}/{results['total']})")
    print("(Heuristic: 'pass' = output contains a valid diff hunk)")


def _export_gguf(adapter_path: Path) -> None:
    """Merge LoRA adapter into base model and export as GGUF for Ollama."""
    print("\nExporting to GGUF (requires llama.cpp installed)...")
    print("Step 1: Merge adapter into base model")
    merge_script = REPO_ROOT / "bin" / "_merge_lora.py"
    if not merge_script.exists():
        print("  Creating merge script...")
        merge_script.write_text(
            "#!/usr/bin/env python3\n"
            "# Merge LoRA adapter into base model weights\n"
            "import sys\n"
            "from pathlib import Path\n"
            "from peft import AutoPeftModelForCausalLM\n"
            "adapter = Path(sys.argv[1])\n"
            "merged_dir = adapter.parent / 'merged'\n"
            "model = AutoPeftModelForCausalLM.from_pretrained(str(adapter), device_map='cpu')\n"
            "model = model.merge_and_unload()\n"
            "model.save_pretrained(str(merged_dir))\n"
            "print(f'Merged model saved to {merged_dir}')\n"
        )
    result = subprocess.run([sys.executable, str(merge_script), str(adapter_path)])
    if result.returncode != 0:
        print("Merge failed. Check that peft is installed.")
        return

    merged_dir = adapter_path.parent / "merged"
    gguf_path = adapter_path.parent / "model.gguf"

    print("Step 2: Convert to GGUF with llama.cpp")
    convert_cmd = ["python3", "convert_hf_to_gguf.py", str(merged_dir), "--outfile", str(gguf_path)]
    print(f"  Run: {' '.join(convert_cmd)}")
    print("  (Requires llama.cpp cloned at ~/llama.cpp)")
    print()

    modelfile_path = adapter_path.parent / "Modelfile"
    modelfile_path.write_text(
        f"FROM {gguf_path}\n"
        f"PARAMETER temperature 0.1\n"
        f"PARAMETER num_ctx 8192\n"
        f'SYSTEM "You are a precise code modification assistant. Output unified diffs."\n'
    )
    print(f"Step 3: Load into Ollama")
    print(f"  ollama create qwen25-coder-finetuned -f {modelfile_path}")
    print(f"  ollama run qwen25-coder-finetuned 'Add a health check to domains/media.py'")


def main() -> int:
    parser = argparse.ArgumentParser(description="Training cycle: collect → train → eval")
    parser.add_argument("--data", help="Path to pre-collected alpaca.jsonl (skip collection)")
    parser.add_argument("--collect-only", action="store_true")
    parser.add_argument("--train-only", action="store_true", help="Requires --data")
    parser.add_argument("--export-gguf", action="store_true")
    parser.add_argument("--adapter", help="Path to trained adapter (for --export-gguf or --evaluate)")
    parser.add_argument("--out-dir", default=str(REPO_ROOT / "artifacts" / "training_data"))
    parser.add_argument("--no-venv", action="store_true", help="Skip venv isolation (advanced)")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)

    # Collect — works without ML deps; always runs in current interpreter
    if args.data:
        data_path = Path(args.data)
    else:
        data_path = _collect(out_dir, fmt="alpaca")
        if data_path is None:
            return 1

    if args.collect_only:
        return 0

    # Training requires ML deps — ensure venv and re-exec inside it
    if not args.no_venv:
        if not _ensure_venv():
            return 1
        _relaunch_in_venv()  # re-execs under venv Python if not already there

    if not _check_training_deps():
        print("\nDeps not available in current interpreter.")
        print(f"Run directly: {VENV_PYTHON} {Path(__file__).name} {' '.join(sys.argv[1:])}")
        return 1

    adapter_path = None
    if args.adapter:
        adapter_path = Path(args.adapter)
    elif not args.export_gguf:
        adapter_path = _train(data_path)
        if adapter_path is None:
            return 1

    # Evaluate
    if adapter_path and data_path:
        _evaluate(adapter_path, data_path)

    # Export
    if args.export_gguf:
        if not adapter_path:
            print("--export-gguf requires --adapter <path>")
            return 1
        _export_gguf(adapter_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
