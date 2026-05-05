#!/usr/bin/env python3
"""Build a structured Aider trace corpus from local telemetry.

Inputs:
  - artifacts/execution_metrics.jsonl
  - artifacts/aider_runs/**/metadata.json
  - artifacts/executions/*.json
  - artifacts/aider_runs/verifier_events.jsonl

Outputs:
  - artifacts/aider_trace_corpus_v0.parquet
  - artifacts/aider_trace_corpus_v0.md

The corpus is local-only. It is intended for analysis, taxonomy building,
and prompt/verifier hardening on this repository's own traces.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = REPO_ROOT / "artifacts"
DEFAULT_OUT = ARTIFACTS / "aider_trace_corpus_v0.parquet"
DEFAULT_REPORT = ARTIFACTS / "aider_trace_corpus_v0.md"


@dataclass(frozen=True)
class TraceRow:
    source_type: str
    source_id: str
    source_path: str
    prompt_text: str
    file_state_pre: str
    file_state_post: str
    model: str
    layer1_verdict: str
    layer1_5_verdict: str
    success_boolean: bool
    failure_mode_class: str
    failure_mode_detail: str
    label_confidence: float
    task_type: str
    duration_seconds: float | None
    exit_code: int | None
    record_timestamp: str
    requested_files: str
    changed_files: str
    failure_signatures: str


def read_jsonl(path: Path) -> Iterator[dict]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def sanitize_text(text: object) -> object:
    if isinstance(text, str):
        return text.encode("utf-8", errors="replace").decode("utf-8")
    return text


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def tail_line(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[-1] if lines else text.strip()


def parse_prompt_and_files(command: str) -> tuple[str, list[str]]:
    if not command:
        return "", []
    try:
        tokens = shlex.split(command)
    except ValueError:
        return command.strip(), []
    if "--message" not in tokens:
        return command.strip(), []
    idx = tokens.index("--message")
    prompt = tokens[idx + 1] if idx + 1 < len(tokens) else ""
    files = tokens[idx + 2 :]
    return prompt, [f for f in files if f and not f.startswith("-")]


def parse_git_status(path: Path) -> str:
    text = safe_read_text(path)
    if not text:
        return ""
    parsed: dict[str, object] = {"raw": text}
    lines = [line.rstrip("\n") for line in text.splitlines() if line.strip()]
    if lines:
        parsed["branch"] = lines[0]
        tracked: list[str] = []
        untracked: list[str] = []
        for line in lines[1:]:
            if line.startswith("?? "):
                untracked.append(line[3:])
            elif len(line) > 3:
                tracked.append(line[3:])
        parsed["tracked"] = tracked
        parsed["untracked"] = untracked
    return json.dumps(parsed, ensure_ascii=False, sort_keys=True)


def read_list_file(path: Path) -> list[str]:
    text = safe_read_text(path)
    if not text:
        return []
    return [line.strip() for line in text.splitlines() if line.strip()]


def load_verifier_index() -> dict[tuple[str, str], str]:
    index: dict[tuple[str, str], str] = {}
    for rec in read_jsonl(ARTIFACTS / "aider_runs" / "verifier_events.jsonl"):
        desc = normalize_text(str(rec.get("description", "")))
        file_path = str(rec.get("file_path", ""))
        verdict = str(rec.get("verdict", "UNKNOWN")).upper() or "UNKNOWN"
        if desc:
            index[(desc, file_path)] = verdict
    return index


def match_verifier_verdict(prompt_text: str, requested_files: list[str], verifier_index: dict[tuple[str, str], str]) -> str:
    prompt_norm = normalize_text(tail_line(prompt_text))
    if not prompt_norm:
        return "UNKNOWN"
    # Direct matches first.
    for file_path in requested_files[:3]:
        verdict = verifier_index.get((prompt_norm, file_path))
        if verdict:
            return verdict
    # Fuzzy fallback: same prompt and any file path.
    for (desc_norm, file_path), verdict in verifier_index.items():
        if desc_norm == prompt_norm and (not requested_files or file_path in requested_files):
            return verdict
    # Substring fallback for slightly different prompt text.
    for (desc_norm, file_path), verdict in verifier_index.items():
        if (desc_norm in prompt_norm or prompt_norm in desc_norm) and (
            not requested_files or file_path in requested_files
        ):
            return verdict
    return "UNKNOWN"


def infer_task_type(prompt_text: str, task_type: str | None = None) -> str:
    if task_type:
        return task_type
    text = tail_line(prompt_text).lower()
    if any(
        phrase in text
        for phrase in [
            "add docstring",
            "add a docstring",
            "add docstrings",
            "replace bare except",
            "narrow except",
            "replace 'except:'",
            "fix typo",
            "fix indentation",
            "rename variable",
            "add logging",
            "add log line",
        ]
    ):
        return "mechanical"
    if any(
        phrase in text
        for phrase in [
            "add type hints",
            "add type annotations",
            "annotate types",
            "extract function",
            "extract method",
            "refactor into helper",
            "split into helpers",
            "redesign",
            "rewrite",
            "rearchitect",
            "implement",
            "build",
            "create",
        ]
    ):
        return "inference_heavy"
    return "ambiguous"


def classify_failure(
    *,
    success: bool,
    failure_signatures: list[str],
    error_type: str | None,
    prompt_text: str,
    requested_files: list[str],
    changed_files: list[str],
) -> tuple[str, str, float]:
    """Return (failure_mode_class, detail, confidence)."""

    if success:
        return "success", "", 1.0

    sigset = {sig for sig in failure_signatures if sig}
    prompt_tail = tail_line(prompt_text).lower()
    requested = set(requested_files)
    changed = set(changed_files)
    extra_changes = sorted(changed - requested) if requested and changed else []

    if "timeout" in sigset or error_type == "timeout":
        return "timeout", "timeout signature present", 0.99
    if "unexpected_file_creation" in sigset:
        return "wrong_target", "unexpected_file_creation signature", 0.95
    if extra_changes:
        return "wrong_target", f"changed files outside request: {', '.join(extra_changes[:5])}", 0.9
    if any(
        phrase in prompt_tail
        for phrase in [
            "line ",
            "the bare except",
            "the first bare except",
            "the second bare except",
            "multiple except",
        ]
    ) and any(sig in sigset for sig in {"no_changes", "validation_failed"}) :
        return "target_ambiguous", "ambiguous prompt pattern + non-success outcome", 0.8
    if "no_changes" in sigset or error_type == "no_changes":
        return "no_change", "no_changes signature present", 0.99
    if "validation_failed" in sigset or error_type == "diff_sanity_block":
        return "partial_diff", "validation failed or diff sanity block", 0.95
    if error_type in {"aider_error", "write_failed", "execution_failed"}:
        return "runtime_error", f"{error_type} error_type", 0.9
    if changed:
        return "partial_diff", "changes present but run did not complete cleanly", 0.7
    return "runtime_error", "unclassified failure with no clear diff signal", 0.5


def layer1_verdict_from_row(failure_mode_class: str, success: bool) -> str:
    if success:
        return "PASS"
    if failure_mode_class in {"wrong_target", "target_ambiguous"}:
        return "BLOCK"
    if failure_mode_class in {"no_change", "partial_diff"}:
        return "FAIL"
    if failure_mode_class == "timeout":
        return "BLOCK"
    return "UNKNOWN"


def normalize_record_id(source_type: str, identifier: str) -> str:
    return f"{source_type}:{identifier}"


def collect_local_runs(verifier_index: dict[tuple[str, str], str]) -> list[TraceRow]:
    rows: list[TraceRow] = []
    root = ARTIFACTS / "aider_runs"
    for meta_path in sorted(root.rglob("metadata.json")):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            continue

        source_id = str(meta.get("run_id") or meta_path.parent.name)
        command = str(meta.get("command", ""))
        prompt_text, requested_files = parse_prompt_and_files(command)
        if not prompt_text:
            prompt_text = str(meta.get("label", ""))
        pre_status = parse_git_status(meta_path.parent / "pre_status.txt")
        post_status = parse_git_status(meta_path.parent / "post_status.txt")
        changed_files = read_list_file(meta_path.parent / "diff.files")
        failure_signatures = read_list_file(meta_path.parent / "failure_signatures.txt")
        if not failure_signatures:
            failure_signatures = [str(sig) for sig in (meta.get("failure_signatures") or []) if str(sig)]
        success = str(meta.get("status", "")).lower() == "passed"
        model = str(meta.get("env", {}).get("MODEL") or "")
        if not model:
            model = str(meta.get("env", {}).get("model") or "")
        if not model:
            model = str(meta.get("command", "")).split("--model ")[-1].split(" ")[0] if "--model " in command else ""
        verdict = match_verifier_verdict(prompt_text, requested_files, verifier_index)
        failure_mode, detail, confidence = classify_failure(
            success=success,
            failure_signatures=failure_signatures,
            error_type=None,
            prompt_text=prompt_text,
            requested_files=requested_files,
            changed_files=changed_files,
        )
        rows.append(
            TraceRow(
                source_type="aider_run",
                source_id=normalize_record_id("aider_run", source_id),
                source_path=str(meta_path),
                prompt_text=prompt_text,
                file_state_pre=pre_status,
                file_state_post=post_status,
                model=model,
                layer1_verdict=layer1_verdict_from_row(failure_mode, success),
                layer1_5_verdict=verdict,
                success_boolean=success,
                failure_mode_class=failure_mode,
                failure_mode_detail=detail,
                label_confidence=confidence,
                task_type=infer_task_type(prompt_text, meta.get("task_type")),
                duration_seconds=float(meta.get("duration_sec") or 0.0),
                exit_code=int(meta.get("exit_code") or 0),
                record_timestamp=str(meta.get("start_time") or ""),
                requested_files=json.dumps(requested_files, ensure_ascii=False),
                changed_files=json.dumps(changed_files, ensure_ascii=False),
                failure_signatures=json.dumps(failure_signatures, ensure_ascii=False),
            )
        )
    return rows


def collect_execution_metrics(verifier_index: dict[tuple[str, str], str]) -> list[TraceRow]:
    rows: list[TraceRow] = []
    path = ARTIFACTS / "execution_metrics.jsonl"
    for idx, rec in enumerate(read_jsonl(path), start=1):
        prompt_text = str(rec.get("description", ""))
        success = bool(rec.get("success"))
        error_type = rec.get("error_type")
        failure_signatures = [str(error_type)] if error_type else []
        failure_mode, detail, confidence = classify_failure(
            success=success,
            failure_signatures=failure_signatures,
            error_type=error_type,
            prompt_text=prompt_text,
            requested_files=[],
            changed_files=[],
        )
        rows.append(
            TraceRow(
                source_type="execution_metric",
                source_id=normalize_record_id("execution_metric", str(idx)),
                source_path=str(path),
                prompt_text=prompt_text,
                file_state_pre="",
                file_state_post="",
                model=str(rec.get("model", "")),
                layer1_verdict=layer1_verdict_from_row(failure_mode, success),
                layer1_5_verdict=match_verifier_verdict(prompt_text, [], verifier_index),
                success_boolean=success,
                failure_mode_class=failure_mode,
                failure_mode_detail=detail,
                label_confidence=confidence,
                task_type=str(rec.get("task_type", "")),
                duration_seconds=float(rec.get("duration_seconds") or 0.0),
                exit_code=int(rec.get("exit_code") or 0),
                record_timestamp=str(rec.get("timestamp") or ""),
                requested_files="[]",
                changed_files="[]",
                failure_signatures=json.dumps(failure_signatures, ensure_ascii=False),
            )
        )
    return rows


def collect_execution_artifacts(verifier_index: dict[tuple[str, str], str]) -> list[TraceRow]:
    rows: list[TraceRow] = []
    root = ARTIFACTS / "executions"
    for p in sorted(root.glob("*.json")):
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        prompt_text = str(rec.get("description") or rec.get("task_slug") or p.stem)
        success = bool(rec.get("success"))
        failure_signatures = [str(sig) for sig in (rec.get("failure_signatures") or []) if str(sig)]
        error_type = str(rec.get("error") or "")
        failure_mode, detail, confidence = classify_failure(
            success=success,
            failure_signatures=failure_signatures,
            error_type=error_type if error_type else None,
            prompt_text=prompt_text,
            requested_files=[],
            changed_files=[],
        )
        rows.append(
            TraceRow(
                source_type="execution_artifact",
                source_id=normalize_record_id("execution_artifact", p.stem),
                source_path=str(p),
                prompt_text=prompt_text,
                file_state_pre="",
                file_state_post="",
                model=str(rec.get("model") or rec.get("model_used") or ""),
                layer1_verdict=layer1_verdict_from_row(failure_mode, success),
                layer1_5_verdict=match_verifier_verdict(prompt_text, [], verifier_index),
                success_boolean=success,
                failure_mode_class=failure_mode,
                failure_mode_detail=detail,
                label_confidence=confidence,
                task_type="coding",
                duration_seconds=None,
                exit_code=None,
                record_timestamp="",
                requested_files="[]",
                changed_files="[]",
                failure_signatures=json.dumps(failure_signatures, ensure_ascii=False),
            )
        )
    return rows


def rows_to_df(rows: Iterable[TraceRow]) -> pd.DataFrame:
    df = pd.DataFrame([row.__dict__ for row in rows])
    if df.empty:
        return df
    return df.apply(lambda col: col.map(sanitize_text) if col.dtype == object else col)


def write_report(df: pd.DataFrame, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    lines.append("# Aider Trace Corpus v0")
    lines.append("")
    lines.append(f"- rows: {len(df)}")
    lines.append(f"- sources: {df['source_type'].value_counts().to_dict()}")
    lines.append(f"- success: {int(df['success_boolean'].sum())}")
    lines.append("")
    lines.append("## Failure classes")
    for cls, count in df["failure_mode_class"].value_counts().sort_values(ascending=False).items():
        lines.append(f"- {cls}: {int(count)}")
    lines.append("")
    lines.append("## Layer verdicts")
    lines.append(f"- layer1 PASS: {(df['layer1_verdict'] == 'PASS').sum()}")
    lines.append(f"- layer1 BLOCK: {(df['layer1_verdict'] == 'BLOCK').sum()}")
    lines.append(f"- layer1.5 AGREE: {(df['layer1_5_verdict'] == 'AGREE').sum()}")
    lines.append(f"- layer1.5 DISAGREE: {(df['layer1_5_verdict'] == 'DISAGREE').sum()}")
    lines.append(f"- layer1.5 UNKNOWN: {(df['layer1_5_verdict'] == 'UNKNOWN').sum()}")
    lines.append("")
    lines.append("## Confidence")
    lines.append(
        f"- mean label confidence: {df['label_confidence'].mean():.2f}"
        if len(df)
        else "- mean label confidence: n/a"
    )
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Aider trace corpus")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Output Parquet path")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Output Markdown summary path")
    parser.add_argument("--skip-execution-metrics", action="store_true")
    parser.add_argument("--skip-aider-runs", action="store_true")
    parser.add_argument("--skip-executions", action="store_true")
    args = parser.parse_args()

    verifier_index = load_verifier_index()
    rows: list[TraceRow] = []
    if not args.skip_aider_runs:
        rows.extend(collect_local_runs(verifier_index))
    if not args.skip_execution_metrics:
        rows.extend(collect_execution_metrics(verifier_index))
    if not args.skip_executions:
        rows.extend(collect_execution_artifacts(verifier_index))

    df = rows_to_df(rows)
    if df.empty:
        raise SystemExit("no trace rows discovered")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)
    write_report(df, Path(args.report))

    print(f"[aider-trace] wrote {len(df)} rows to {out_path}")
    print(f"[aider-trace] wrote report to {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
