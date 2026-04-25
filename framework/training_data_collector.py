"""Collect real training examples from executor history.

A "real" training example requires:
  1. success=True in the execution artifact
  2. A git commit that actually introduces .py file changes (not just a status flip)
  3. A non-trivial diff (>3 lines added)

Before commit 4ec96e3 (2026-04-24) the executor used --no-auto-commits and
reported the pre-run HEAD as commit_hash, so most old artifacts are spurious.
This collector validates each commit before including it.

Produces Alpaca-format JSONL:
  {"instruction": "...", "input": "", "output": "..."}
  instruction = task description (from slug or metrics JSONL)
  output      = unified diff of the aider commit
"""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterator


REPO_ROOT = Path(__file__).parent.parent
ARTIFACTS = REPO_ROOT / "artifacts"


@dataclass
class TrainingExample:
    instruction: str
    input: str
    output: str
    meta: dict


def _git_diff(commit: str, repo_root: Path) -> str | None:
    """Return unified diff for a commit, or None if not useful."""
    result = subprocess.run(
        ["git", "diff", f"{commit}^..{commit}"],
        capture_output=True, text=True, cwd=repo_root, timeout=15,
    )
    if result.returncode != 0:
        return None
    diff = result.stdout.strip()
    if not diff:
        return None
    return diff


def _is_real_code_diff(diff: str) -> bool:
    """True if the diff contains meaningful .py additions (not just status flips)."""
    if ".py" not in diff:
        return False
    added_lines = sum(
        1 for line in diff.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    )
    return added_lines >= 3


def _slug_to_description(slug: str) -> str:
    """Convert aider-task slug back to a readable instruction."""
    return slug.replace("-", " ").strip()


def _load_metrics_index(metrics_path: Path) -> dict[str, str]:
    """Build slug → full_description index from execution_metrics.jsonl."""
    index: dict[str, str] = {}
    if not metrics_path.exists():
        return index
    for line in metrics_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            desc = rec.get("description", "")
            if desc:
                # Reproduce the slug: first ~50 chars, lowercase, non-alnum → dash
                slug = re.sub(r"[^a-z0-9]+", "-", desc.lower())[:50].strip("-")
                index[slug] = desc
        except json.JSONDecodeError:
            pass
    return index


def collect(
    artifacts_dir: Path | None = None,
    repo_root: Path | None = None,
    min_diff_lines: int = 3,
) -> Iterator[TrainingExample]:
    """Yield validated training examples from executor artifacts."""
    artifacts_dir = artifacts_dir or ARTIFACTS
    repo_root = repo_root or REPO_ROOT

    executions_dir = artifacts_dir / "executions"
    if not executions_dir.exists():
        return

    metrics_index = _load_metrics_index(artifacts_dir / "execution_metrics.jsonl")

    for artifact_path in sorted(executions_dir.glob("*.json")):
        try:
            data = json.loads(artifact_path.read_text())
        except (OSError, json.JSONDecodeError):
            continue

        if not data.get("success"):
            continue
        commit = data.get("commit_hash", "")
        if not commit or len(commit) < 8:
            continue

        diff = _git_diff(commit, repo_root)
        if diff is None:
            continue
        if not _is_real_code_diff(diff):
            continue

        added = sum(
            1 for line in diff.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        )
        if added < min_diff_lines:
            continue

        slug = data.get("task_slug", "")
        description = metrics_index.get(slug) or _slug_to_description(slug)

        yield TrainingExample(
            instruction=description,
            input="",
            output=diff,
            meta={
                "artifact": artifact_path.name,
                "commit": commit[:12],
                "model": data.get("model", "unknown"),
                "diff_lines_added": added,
            },
        )


def write_alpaca_jsonl(examples: list[TrainingExample], out_path: Path) -> int:
    """Write examples to Alpaca-format JSONL. Returns count written."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for ex in examples:
        lines.append(json.dumps({
            "instruction": ex.instruction,
            "input": ex.input,
            "output": ex.output,
        }, ensure_ascii=False))
    out_path.write_text("\n".join(lines) + "\n")
    return len(lines)


def write_chatml_jsonl(examples: list[TrainingExample], out_path: Path) -> int:
    """Write examples as ChatML conversations for chat-tuned models."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for ex in examples:
        conv = {
            "conversations": [
                {"from": "human", "value": ex.instruction},
                {"from": "gpt", "value": ex.output},
            ]
        }
        lines.append(json.dumps(conv, ensure_ascii=False))
    out_path.write_text("\n".join(lines) + "\n")
    return len(lines)
