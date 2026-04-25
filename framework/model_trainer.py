"""LoRA fine-tuning of a local Qwen2.5-Coder model.

PREREQUISITES (must install before this module works):
    pip install torch transformers peft datasets accelerate bitsandbytes

For Apple Silicon (faster training via MPS):
    pip install torch --index-url https://download.pytorch.org/whl/cpu
    # MPS is auto-detected; no CUDA needed

The base model must be downloaded from HuggingFace, NOT from Ollama.
Ollama uses GGUF (quantized inference format) which cannot be LoRA-trained.

    from huggingface_hub import snapshot_download
    snapshot_download("Qwen/Qwen2.5-Coder-7B-Instruct", local_dir="~/.cache/qwen25-coder-7b")

Disk space: ~14 GB for 7B model in bf16.

After training, to use with Ollama:
    python3 bin/run_training_cycle.py --export-gguf   # requires llama.cpp
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


REPO_ROOT = Path(__file__).parent.parent


@dataclass
class TrainingConfig:
    base_model: str = "Qwen/Qwen2.5-Coder-7B-Instruct"
    # LoRA rank: 8 is standard. Higher = more capacity, more VRAM.
    lora_r: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.05
    # Target modules for Qwen2 architecture
    lora_target_modules: tuple = ("q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj")
    # Training hyperparameters
    learning_rate: float = 2e-4
    num_epochs: int = 3
    batch_size: int = 1          # 1 for Apple Silicon MPS (low VRAM)
    grad_accumulation: int = 8   # effective batch = 8
    max_seq_length: int = 2048
    warmup_ratio: float = 0.03
    # Evaluation
    eval_split: float = 0.1      # hold out 10% for eval
    # Output
    output_dir: str = "artifacts/lora_adapter"


def _check_deps() -> list[str]:
    """Return list of missing dependency names."""
    missing = []
    for pkg in ("torch", "transformers", "peft", "datasets"):
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    return missing


def _alpaca_to_prompt(instruction: str, output: str) -> str:
    """Format an Alpaca example as a model prompt."""
    return (
        f"Below is a coding task. Produce the unified diff that implements it.\n\n"
        f"### Task:\n{instruction}\n\n"
        f"### Diff:\n{output}"
    )


def train(
    data_path: Path,
    config: Optional[TrainingConfig] = None,
    repo_root: Path | None = None,
) -> Path:
    """Fine-tune a LoRA adapter on executor training data.

    Args:
        data_path: Path to alpaca.jsonl produced by collect_training_data.py
        config: Training configuration (uses defaults if None)
        repo_root: Repository root for output paths

    Returns:
        Path to the saved adapter directory

    Raises:
        ImportError: If required packages are not installed
        RuntimeError: If not enough training examples
    """
    missing = _check_deps()
    if missing:
        raise ImportError(
            f"Missing packages: {', '.join(missing)}\n"
            f"Install with: pip install {' '.join(missing)} accelerate bitsandbytes"
        )

    import torch
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model, TaskType
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        TrainingArguments,
        Trainer,
        DataCollatorForLanguageModeling,
    )

    config = config or TrainingConfig()
    repo_root = repo_root or REPO_ROOT
    out_dir = repo_root / config.output_dir

    # Load data
    records = [json.loads(line) for line in data_path.read_text().splitlines() if line.strip()]
    if len(records) < 5:
        raise RuntimeError(
            f"Only {len(records)} training examples — need at least 5. "
            f"Run more executor tasks to accumulate real commits, then re-collect."
        )

    print(f"Training on {len(records)} examples with {config.base_model}")

    # Format prompts
    texts = [_alpaca_to_prompt(r["instruction"], r["output"]) for r in records]

    # Split train/eval
    split_idx = max(1, int(len(texts) * (1 - config.eval_split)))
    train_texts, eval_texts = texts[:split_idx], texts[split_idx:]
    print(f"Train: {len(train_texts)}, Eval: {len(eval_texts)}")

    # Detect device
    if torch.cuda.is_available():
        device = "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    print(f"Device: {device}")

    # Load tokenizer and model
    print(f"Loading {config.base_model} (this downloads ~14GB on first run)...")
    tokenizer = AutoTokenizer.from_pretrained(config.base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        config.base_model,
        torch_dtype=torch.bfloat16,
        device_map="auto" if device != "mps" else None,
        trust_remote_code=True,
    )
    if device == "mps":
        model = model.to("mps")

    # Apply LoRA
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        lora_dropout=config.lora_dropout,
        target_modules=list(config.lora_target_modules),
        bias="none",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Tokenize
    def tokenize(batch):
        return tokenizer(
            batch["text"],
            truncation=True,
            max_length=config.max_seq_length,
            padding=False,
        )

    train_ds = Dataset.from_dict({"text": train_texts}).map(tokenize, batched=True, remove_columns=["text"])
    eval_ds = Dataset.from_dict({"text": eval_texts}).map(tokenize, batched=True, remove_columns=["text"])

    # Training args
    training_args = TrainingArguments(
        output_dir=str(out_dir / "checkpoints"),
        num_train_epochs=config.num_epochs,
        per_device_train_batch_size=config.batch_size,
        gradient_accumulation_steps=config.grad_accumulation,
        learning_rate=config.learning_rate,
        warmup_ratio=config.warmup_ratio,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        logging_steps=10,
        report_to="none",
        fp16=(device == "cuda"),
        bf16=(device in ("cpu", "mps")),
        dataloader_pin_memory=(device == "cuda"),
        use_mps_device=(device == "mps"),
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
    )

    print("Training...")
    trainer.train()

    # Save adapter only (not full model — much smaller)
    adapter_path = out_dir / "adapter"
    model.save_pretrained(str(adapter_path))
    tokenizer.save_pretrained(str(adapter_path))
    print(f"Adapter saved to: {adapter_path}")

    return adapter_path


def evaluate_on_tasks(
    adapter_path: Path,
    eval_tasks: list[dict],
    base_model: str = "Qwen/Qwen2.5-Coder-7B-Instruct",
) -> dict:
    """Run eval tasks through the fine-tuned model. Returns pass/total counts."""
    missing = _check_deps()
    if missing:
        raise ImportError(f"Missing: {', '.join(missing)}")

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(str(adapter_path))
    base = AutoModelForCausalLM.from_pretrained(base_model, torch_dtype=torch.bfloat16, device_map="auto")
    model = PeftModel.from_pretrained(base, str(adapter_path))
    model.eval()

    results = {"pass": 0, "total": len(eval_tasks), "outputs": []}
    for task in eval_tasks:
        prompt = _alpaca_to_prompt(task["instruction"], "")
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=512, do_sample=False)
        generated = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        # Simple heuristic: generated contains a diff hunk
        passed = "@@" in generated or "+++" in generated
        if passed:
            results["pass"] += 1
        results["outputs"].append({"instruction": task["instruction"], "output": generated, "passed": passed})

    results["pass_rate"] = results["pass"] / results["total"] if results["total"] else 0
    return results
