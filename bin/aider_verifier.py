#!/usr/bin/env python3
"""
aider_verifier.py — Layer 1.5 dual-loop verifier (D-17-110).

Calls qwen2.5-coder:14b (default) on Mac Mini local Ollama to review an Aider diff
and determine whether it matches the stated task description. Model is configurable:
  AIDER_VERIFIER_MODEL=deepseek-coder-v2:16b-lite-instruct-q4_K_M (Mac Studio, when WP-03 lands)
  AIDER_VERIFIER_API_BASE=http://192.168.10.142:11434 (when Mac Studio is externally reachable)

Exit codes:
  0  AGREE      — diff matches task description
  1  DISAGREE   — diff does not match; see REASON in output
  2  ERROR       — model unreachable, API error, or unrecoverable failure
  3  AMBIGUOUS   — model responded but verdict could not be parsed

Usage:
  git diff <file> | python3 bin/aider_verifier.py \\
      --description "Add docstring to parse_config" \\
      --file-path config/parser.py \\
      --diff-stdin
"""

import argparse
import ast
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
PROMPT_TEMPLATE = REPO_ROOT / "config/prompts/library/v1.0.0/07-deepseek-verifier-prompt.md"
VERIFIER_LOG = REPO_ROOT / "artifacts/aider_runs/verifier_events.jsonl"

DEFAULT_MODEL = "deepseek-coder-v2:16b-lite-instruct-q4_K_M"
DEFAULT_API_BASE = "http://192.168.10.142:11434"

MODEL = os.environ.get("AIDER_VERIFIER_MODEL", DEFAULT_MODEL)
API_BASE = os.environ.get("AIDER_VERIFIER_API_BASE", DEFAULT_API_BASE)
TIMEOUT = int(os.environ.get("AIDER_VERIFIER_TIMEOUT", "60"))
MAX_RETRIES = 1


def _setting_source(env_name: str) -> str:
    return "env" if os.environ.get(env_name) else "default"


def count_definitions(path: str) -> int:
    """Count def/class lines in a file. Returns 0 on any error."""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
        count = 0
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("def ") or stripped.startswith("class "):
                count += 1
        return count
    except Exception:
        return 0


def count_definitions_from_head(rel_path: str) -> int:
    """Count def/class lines in git HEAD version of a file."""
    try:
        result = subprocess.run(
            ["git", "show", f"HEAD:{rel_path}"],
            capture_output=True, text=True,
            cwd=REPO_ROOT,
        )
        if result.returncode != 0:
            return 0
        count = 0
        for line in result.stdout.splitlines():
            stripped = line.strip()
            if stripped.startswith("def ") or stripped.startswith("class "):
                count += 1
        return count
    except Exception:
        return 0


def load_prompt_template() -> str:
    """Extract the user input template and system role from the prompt file."""
    try:
        text = PROMPT_TEMPLATE.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise RuntimeError(f"Prompt template not found: {PROMPT_TEMPLATE}")

    # Extract system role (between "# System Role" and next "# " heading)
    system_match = re.search(
        r"# System Role\n\n(.*?)(?=\n# )", text, re.DOTALL
    )
    system_role = system_match.group(1).strip() if system_match else (
        "You are a code review assistant. Determine whether a diff matches a task description."
    )

    return system_role


def build_prompt(system_role: str, description: str, file_path: str,
                 diff: str, orig_count: int, new_count: int) -> str:
    """Build a raw prompt string for /api/generate (works with both base and instruct models)."""
    count_note = ""
    if orig_count > 0 and new_count != orig_count:
        count_note = (
            f"\nWARNING: Function/class count changed from {orig_count} to {new_count}. "
            f"This is suspicious if the task only asked to add docstrings or make small edits.\n"
        )
    return (
        f"{system_role}\n\n"
        f"TASK: {description}\n"
        f"FILE: {file_path}\n"
        f"ORIGINAL FUNCTION/CLASS COUNT: {orig_count}\n"
        f"NEW FUNCTION/CLASS COUNT: {new_count}{count_note}\n"
        f"DIFF:\n{diff}\n\n"
        f"Does this diff do exactly what the TASK asked — no more, no less?\n"
        f"DISAGREE if: function count changed unexpectedly, function bodies are duplicated, "
        f"logic was modified beyond scope, or the change is disproportionately large for the task.\n"
        f"Answer using this exact format (no other text):\n"
        f"VERDICT: AGREE\n"
        f"REASON: <why>\n\n"
        f"or:\n\n"
        f"VERDICT: DISAGREE\n"
        f"REASON: <why>\n\n"
        f"VERDICT:"
    )


def call_model(prompt: str, attempt: int = 1) -> tuple[str, float]:
    """Call Ollama /api/generate. Returns (raw_response_text, duration_sec)."""
    url = f"{API_BASE.rstrip('/')}/api/generate"
    payload = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0, "num_predict": 80, "stop": ["\n\n", "TASK:", "FILE:"]},
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read().decode("utf-8")
        duration = time.monotonic() - t0
        data = json.loads(body)
        raw = data.get("response", "").strip()
        return raw, duration
    except urllib.error.URLError as e:
        duration = time.monotonic() - t0
        raise ConnectionError(
            f"Ollama unreachable at {API_BASE} (attempt {attempt}): {e}"
        ) from e
    except json.JSONDecodeError as e:
        duration = time.monotonic() - t0
        raise ValueError(f"Bad JSON response from Ollama (attempt {attempt}): {e}") from e


def parse_verdict(raw: str) -> tuple[str, str]:
    """Parse VERDICT and REASON lines. Returns (verdict, reason)."""
    # The assistant message was primed with "VERDICT:" so the model continues from there.
    # Prepend it back to ensure the regex finds it.
    full = "VERDICT:" + raw if not raw.strip().upper().startswith("VERDICT") else raw
    # Normalize: strip think tags (DeepSeek sometimes wraps reasoning)
    cleaned = re.sub(r"<think>.*?</think>", "", full, flags=re.DOTALL).strip()

    verdict_match = re.search(r"VERDICT:\s*(AGREE|DISAGREE)", cleaned, re.IGNORECASE)
    reason_match = re.search(r"REASON:\s*(.+)", cleaned)

    if not verdict_match:
        return "UNKNOWN", cleaned[:120]

    verdict = verdict_match.group(1).upper()
    reason = reason_match.group(1).strip()[:120] if reason_match else "(no reason)"
    return verdict, reason


def append_log(record: dict) -> None:
    """Append a JSONL record to the verifier events log."""
    try:
        VERIFIER_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(VERIFIER_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        pass


def run(description: str, file_path: str, diff: str, quiet: bool = False) -> int:
    orig_count = count_definitions_from_head(file_path)
    new_count = count_definitions(file_path)

    try:
        system_role = load_prompt_template()
    except RuntimeError as e:
        print(f"[aider-verifier] ERROR: {e}", file=sys.stderr)
        return 2

    prompt = build_prompt(system_role, description, file_path, diff,
                          orig_count, new_count)

    raw = ""
    duration = 0.0
    last_error = ""

    for attempt in range(1, MAX_RETRIES + 2):
        try:
            raw, duration = call_model(prompt, attempt)
            break
        except (ConnectionError, ValueError) as e:
            last_error = str(e)
            if attempt <= MAX_RETRIES:
                time.sleep(2)
                continue
            # All retries exhausted
            append_log({
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "description": description[:120],
                "file_path": file_path,
                "verdict": "ERROR",
                "reason": last_error[:200],
                "model_response_raw": "",
                "duration_sec": duration,
                "orig_count": orig_count,
                "new_count": new_count,
                "model": MODEL,
            })
            print(f"[aider-verifier] ERROR: {last_error}", file=sys.stderr)
            return 2

    verdict, reason = parse_verdict(raw)

    log_record = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "description": description[:120],
        "file_path": file_path,
        "verdict": verdict,
        "reason": reason,
        "model_response_raw": raw[:500],
        "duration_sec": round(duration, 2),
        "orig_count": orig_count,
        "new_count": new_count,
        "model": MODEL,
    }
    append_log(log_record)

    if verdict == "AGREE":
        if quiet:
            print(f"[aider-verifier] verifier=AGREE ({duration:.1f}s)")
        else:
            print(f"[aider-verifier] dual-loop=AGREE")
            print(f"[aider-verifier] REASON: {reason}")
        return 0
    elif verdict == "DISAGREE":
        if quiet:
            print(f"[aider-verifier] verifier=DISAGREE: {reason}")
        else:
            print(f"[aider-verifier] dual-loop=DISAGREE")
            print(f"[aider-verifier] REASON: {reason}")
        return 1
    else:
        print(f"[aider-verifier] AMBIGUOUS — could not parse verdict from model response")
        print(f"[aider-verifier] Raw response: {raw[:200]}")
        return 3


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Layer 1.5 dual-loop verifier — reviews Aider diffs against task description"
    )
    parser.add_argument("--description", required=True, help="Task description given to Aider")
    parser.add_argument("--file-path", required=True, help="Changed file path (relative to repo root)")
    parser.add_argument("--diff-stdin", action="store_true",
                        help="Read diff from stdin")
    parser.add_argument("--diff", default="", help="Diff text (alternative to --diff-stdin)")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Compact single-line output")
    parser.add_argument("--api-base", default=None,
                        help="Override Ollama API base URL (default: OLLAMA_API_BASE or Mac Studio)")
    args = parser.parse_args()

    model_source = _setting_source("AIDER_VERIFIER_MODEL")
    api_source = _setting_source("AIDER_VERIFIER_API_BASE")

    if args.api_base:
        global API_BASE
        API_BASE = args.api_base
        api_source = "arg"

    print(
        f"[aider-verifier] config: api_base={API_BASE} ({api_source}) model={MODEL} ({model_source})",
        file=sys.stderr,
    )

    if args.diff_stdin:
        diff = sys.stdin.read()
    else:
        diff = args.diff

    if not diff.strip():
        print("[aider-verifier] ERROR: no diff provided (use --diff-stdin or --diff)", file=sys.stderr)
        return 2

    return run(args.description, args.file_path, diff, quiet=args.quiet)


if __name__ == "__main__":
    sys.exit(main())
