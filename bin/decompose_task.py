#!/usr/bin/env python3
"""Decompose complex tasks into sequential subtasks using local Ollama."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import requests


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OLLAMA_BASE = os.environ.get("OLLAMA_API_BASE", "http://127.0.0.1:11434").rstrip("/")
DEFAULT_MODEL = os.environ.get("DECOMPOSE_TASK_MODEL", "qwen2.5-coder:14b")


def build_prompt(task: str, files: list[str], max_subtasks: int) -> str:
    """Build a decomposition prompt for local Ollama."""
    files_block = "\n".join(f"- {path}" for path in files) if files else "- (none)"
    return (
        "You are a senior coding planner. Break the task into sequential, bounded subtasks.\n"
        "Rules:\n"
        f"- Return exactly 1 to {max_subtasks} numbered subtasks.\n"
        "- Keep each subtask small, concrete, and ordered.\n"
        "- Prefer implementation order: analysis, code changes, integration, tests.\n"
        "- Do not include explanations, markdown bullets, or extra prose.\n"
        "- Each subtask should fit on one line.\n\n"
        f"Task:\n{task}\n\n"
        f"Primary files:\n{files_block}\n"
    )


def call_ollama(prompt: str, model: str, api_base: str, timeout: int = 60) -> str:
    """Call local Ollama /api/generate and return response text."""
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
        },
    }
    response = requests.post(
        f"{api_base}/api/generate",
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()
    return str(data.get("response", "")).strip()


def parse_numbered_plan(text: str) -> list[str]:
    """Extract a numbered plan from model output."""
    items: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = re.match(r"^\s*(\d+)[\).\:-]\s*(.+?)\s*$", line)
        if match:
            item = match.group(2).strip()
            if item:
                items.append(item)
            continue
        if line and not line.startswith(("-", "*")) and len(items) == 0:
            # Accept a plain line if the model omitted numbering.
            items.append(line)
    return items


def heuristic_plan(task: str) -> list[str]:
    """Fallback bounded plan when Ollama is unavailable."""
    lowered = task.lower()
    plan = ["Clarify the target scope and impacted files"]

    if any(word in lowered for word in ["refactor", "rewrite", "async", "pool", "pooling"]):
        plan.append("Refactor the primary domain or connector in a small, isolated step")
    if "test" not in lowered:
        plan.append("Add or update tests for the new behavior")
    plan.append("Run focused validation on the changed path")
    return plan[:4]


def format_plan(items: list[str]) -> str:
    return "\n".join(f"{i}. {item}" for i, item in enumerate(items, start=1))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Decompose a complex task into sequential subtasks using local Ollama.")
    parser.add_argument("task", help="Task description to decompose.")
    parser.add_argument("files", nargs="*", help="Optional primary files for context.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model to use.")
    parser.add_argument("--api-base", default=DEFAULT_OLLAMA_BASE, help="Ollama API base URL.")
    parser.add_argument("--max-subtasks", type=int, default=4, help="Maximum number of subtasks to return.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of numbered text.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    prompt = build_prompt(args.task, args.files, max(1, args.max_subtasks))

    try:
        response_text = call_ollama(prompt, args.model, args.api_base)
        subtasks = parse_numbered_plan(response_text)
        if not subtasks:
            subtasks = heuristic_plan(args.task)
    except Exception:
        subtasks = heuristic_plan(args.task)

    subtasks = subtasks[: max(1, args.max_subtasks)]

    if args.json:
        payload = {
            "task": args.task,
            "files": args.files,
            "model": args.model,
            "subtasks": subtasks,
        }
        print(json.dumps(payload, indent=2))
    else:
        print(format_plan(subtasks))

    return 0


if __name__ == "__main__":
    sys.exit(main())
