#!/usr/bin/env python3
"""Review current git changes with local Ollama before proceeding."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import requests


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OLLAMA_BASE = os.environ.get("OLLAMA_API_BASE", "http://127.0.0.1:11434").rstrip("/")
DEFAULT_MODEL = os.environ.get("REVIEW_CHANGES_MODEL", "qwen2.5-coder:14b")
DEFAULT_DIFF_LIMIT = int(os.environ.get("REVIEW_CHANGES_DIFF_LIMIT", "40000"))


def git_diff(repo_root: Path) -> tuple[str, str]:
    """Return the current git diff and stat summary."""
    stat = subprocess.run(
        ["git", "diff", "--stat"],
        capture_output=True,
        text=True,
        cwd=repo_root,
        check=False,
    ).stdout.strip()
    diff = subprocess.run(
        ["git", "diff", "--no-ext-diff", "--unified=3"],
        capture_output=True,
        text=True,
        cwd=repo_root,
        check=False,
    ).stdout
    return stat, diff


def build_prompt(stat: str, diff: str, diff_limit: int) -> str:
    """Build a focused review prompt."""
    truncated = diff[:diff_limit]
    suffix = ""
    if len(diff) > diff_limit:
        suffix = f"\n\n[Diff truncated at {diff_limit} characters]"

    return (
        "Review the following git diff for security issues, bugs, regressions, and style problems.\n"
        "Be concise and concrete.\n"
        "Return findings as short bullet lines with severity and file/line references when possible.\n"
        "If there are no issues, say 'No issues found.'\n"
        "Do not suggest unrelated refactors.\n\n"
        f"Diff stat:\n{stat or '(no stat)'}\n\n"
        f"Diff:\n{truncated}{suffix}\n"
    )


def call_ollama(prompt: str, model: str, api_base: str, timeout: int = 90) -> str:
    """Call local Ollama /api/generate for review."""
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
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


def print_review(review_text: str) -> None:
    """Print the model review in a readable format."""
    print("\n[Ollama Review]")
    print("-" * 70)
    print(review_text.strip() or "No issues found.")
    print("-" * 70)


def prompt_user() -> bool:
    """Ask whether to proceed or stop for fixes."""
    while True:
        answer = input("Proceed with these changes? [y]es / [f]ix / [n]o: ").strip().lower()
        if answer in {"y", "yes"}:
            return True
        if answer in {"f", "fix", "n", "no"}:
            return False


def review_current_changes(
    repo_root: Path = REPO_ROOT,
    *,
    model: str = DEFAULT_MODEL,
    api_base: str = DEFAULT_OLLAMA_BASE,
    diff_limit: int = DEFAULT_DIFF_LIMIT,
    interactive: bool = True,
) -> dict[str, Any]:
    """Review current repository changes and optionally prompt the user."""
    stat, diff = git_diff(repo_root)
    prompt = build_prompt(stat, diff, diff_limit)

    try:
        review_text = call_ollama(prompt, model, api_base)
        source = "ollama"
    except Exception as exc:  # noqa: BLE001
        review_text = f"Review unavailable: {exc}"
        source = "fallback"

    print_review(review_text)

    proceed = True
    if interactive and sys.stdin.isatty():
        proceed = prompt_user()

    return {
        "proceed": proceed,
        "review": review_text,
        "source": source,
        "diff_stat": stat,
        "diff_len": len(diff),
        "model": model,
        "api_base": api_base,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review current git changes with local Ollama.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model to use.")
    parser.add_argument("--api-base", default=DEFAULT_OLLAMA_BASE, help="Ollama API base URL.")
    parser.add_argument("--diff-limit", type=int, default=DEFAULT_DIFF_LIMIT, help="Max diff characters to send.")
    parser.add_argument("--json", action="store_true", help="Emit JSON result.")
    parser.add_argument("--non-interactive", action="store_true", help="Do not prompt for proceed/fix.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = review_current_changes(
        model=args.model,
        api_base=args.api_base,
        diff_limit=args.diff_limit,
        interactive=not args.non_interactive,
    )

    if args.json:
        print(json.dumps(result, indent=2))

    return 0 if result["proceed"] else 1


if __name__ == "__main__":
    sys.exit(main())
