# Training Loop — LoRA Fine-Tuning Guide

## Architecture: Three Isolated Environments

```
┌─────────────────────────────────────────────────────────────┐
│ aider 0.86.2                                                │
│ /Users/admin/.local/share/uv/tools/aider-chat/bin/python   │
│ Managed by: uv (completely isolated)                        │
│ Do NOT install anything here                                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ executor / repo Python                                      │
│ /usr/bin/python3  (system Python 3.9)                      │
│ Deps: requests, PyYAML, pathlib — NO ML libs               │
│ Do NOT install torch/transformers here                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ training-env  ~/training-env                                │
│ /opt/homebrew/bin/python3.12 (Python 3.12)                 │
│ Deps: torch 2.11, transformers 5.6, peft 0.19, datasets    │
│ Used only by: bin/run_training_cycle.py                     │
└─────────────────────────────────────────────────────────────┘
```

## Why Isolation Is Required

**The conflict:** `aider-chat` (in its uv env) and `transformers` both depend on
`huggingface-hub`, but require incompatible versions. Installing `transformers`
into any shared Python environment will break whichever package resolves first.

**The fix:** `~/training-env` is a dedicated Python 3.12 venv. `run_training_cycle.py`
auto-detects if it's running outside the venv and re-execs itself inside it. You
never need to activate it manually for normal use.

## Quick Start

```bash
# Collect training data from executor history (no ML deps needed)
python3 bin/run_training_cycle.py --collect-only

# Full training cycle (auto-uses ~/training-env)
python3 bin/run_training_cycle.py

# Or with pre-collected data
python3 bin/run_training_cycle.py --data artifacts/training_data/alpaca.jsonl
```

## Manual Venv Activation (for debugging)

```bash
source ~/training-env/bin/activate

# Now you can import training deps directly
python -c "import torch, transformers, peft; print('all good')"

# Run training manually
python bin/run_training_cycle.py --no-venv --data artifacts/training_data/alpaca.jsonl

deactivate
```

## What the Training Loop Does

### Step 1: Collect (`framework/training_data_collector.py`)

Scans `artifacts/executions/*.json` for:
- `success=True` — executor reported success
- A git commit where HEAD actually advanced (rules out pre-commit-4ec96e3 spurious successes)
- The commit diff contains `.py` file changes with ≥3 added lines

Produces `artifacts/training_data/alpaca.jsonl`:
```json
{"instruction": "Create new file domains/video_quality.py ...", "input": "", "output": "diff --git a/domains/video_quality.py ..."}
```

### Step 2: Train (`framework/model_trainer.py`)

LoRA fine-tuning on `Qwen/Qwen2.5-Coder-7B-Instruct` (HuggingFace weights).

**Critical:** This is NOT the Ollama GGUF model. Ollama distributes quantized
inference weights that cannot be LoRA-trained. The HuggingFace model (~14 GB)
is downloaded automatically on first run.

```
LoRA config: r=8, alpha=16, target=q/v/k/o/gate/up/down proj
Device:      MPS (Apple Silicon) → auto-detected
Adapter:     artifacts/lora_adapter/adapter/ (~100 MB, not 14 GB)
```

### Step 3: Evaluate

Runs held-out examples through the fine-tuned model. Heuristic pass: output
contains a valid unified diff hunk (`@@` marker present).

### Step 4: Export to Ollama (optional, requires llama.cpp)

```bash
python3 bin/run_training_cycle.py --export-gguf --adapter artifacts/lora_adapter/adapter

# Then load into Ollama:
ollama create qwen25-coder-finetuned -f artifacts/lora_adapter/Modelfile
ollama run qwen25-coder-finetuned "Create new file domains/health.py with HealthChecker class"
```

## Training Data Thresholds

| Count | Status |
|-------|--------|
| < 10  | Not enough — run more executor tasks |
| 10-49 | SFT-ready (quick training, may overfit) |
| 50+   | LoRA-ready (stable fine-tuning) |

Training data grows automatically as the executor completes real tasks with
verified git commits. Each successful `auto_execute_roadmap.py` run adds
`(task_description, code_diff)` pairs.

## Dependency Conflict History

**2026-04-24:** `transformers 4.57.6` was accidentally installed into system
Python 3.9 (`pip3 install transformers`). This conflicted with `aider-chat 0.82.3`'s
pinned `huggingface-hub==0.30.2`. Fixed by:
1. Removing `transformers` and `peft` from Python 3.9 (`pip3 uninstall transformers peft`)
2. Creating `~/training-env` (Python 3.12) for all ML deps
3. Updating `run_training_cycle.py` to auto-detect and use the venv

**aider is managed by uv** (`/Users/admin/.local/share/uv/tools/aider-chat/`).
Its environment is completely isolated — `pip3 install` cannot affect it.
Never use `pip3 install aider-chat` to "fix" aider; use `uv tool upgrade aider-chat`.
