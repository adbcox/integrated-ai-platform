"""Manager / control-plane helpers for consuming Phase 2 runtime payload.

All helpers are additive. No legacy keys are removed or renamed.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path
from typing import Any

# ------------------------------------------------------------------ #
# Phase 2 payload detection and extraction helpers                     #
# ------------------------------------------------------------------ #

_PHASE2_REQUIRED_KEYS = frozenset(
    {
        "canonical_session",
        "canonical_jobs",
        "typed_tool_trace",
        "permission_decisions",
        "session_bundle",
        "final_outcome",
    }
)


def _phase2_manager_present(payload: dict[str, Any]) -> bool:
    """Return True iff *payload* contains all Phase 2 runtime keys."""
    return all(k in payload for k in _PHASE2_REQUIRED_KEYS)


def _phase2_manager_tool_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic summary of the typed tool trace in *payload*."""
    trace = payload.get("typed_tool_trace") or []
    tool_names: set[str] = set()
    blocked = 0
    executed = 0
    failed = 0
    for entry in trace:
        try:
            name = str(entry.get("tool_name") or entry.get("contract_name") or "").strip()
            status = str(entry.get("status") or "").strip()
        except Exception:
            continue
        if name:
            tool_names.add(name)
        if status == "blocked":
            blocked += 1
        elif status == "executed":
            executed += 1
        elif status == "failed":
            failed += 1
    return {
        "tool_count": len(tool_names),
        "tool_names_sorted": sorted(tool_names),
        "blocked_count": blocked,
        "executed_count": executed,
        "failed_count": failed,
    }


def _phase2_manager_extract(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract a normalized Phase 2 manager view from a runtime result payload.

    Always returns a complete dict. If the Phase 2 surface is absent the
    ``phase2_payload_present`` flag is ``False`` and summaries are empty.
    """
    _empty_tool_summary: dict[str, Any] = {
        "tool_count": 0,
        "tool_names_sorted": [],
        "blocked_count": 0,
        "executed_count": 0,
        "failed_count": 0,
    }

    if not _phase2_manager_present(payload):
        return {
            "phase2_payload_present": False,
            "canonical_session_summary": {},
            "canonical_job_summaries": [],
            "typed_tool_summary": _empty_tool_summary,
            "permission_decision_count": 0,
            "final_outcome": str(
                payload.get("final_outcome") or payload.get("status") or ""
            ),
        }

    canonical_session: dict[str, Any] = payload.get("canonical_session") or {}
    canonical_jobs: list[Any] = payload.get("canonical_jobs") or []
    permission_decisions: list[Any] = payload.get("permission_decisions") or []

    canonical_session_summary: dict[str, Any] = {
        "session_id": str(canonical_session.get("session_id") or ""),
        "task_id": str(canonical_session.get("task_id") or ""),
        "selected_runtime": str(canonical_session.get("selected_runtime") or ""),
        "selected_model_profile": str(
            canonical_session.get("selected_model_profile") or ""
        ),
        "final_outcome": str(canonical_session.get("final_outcome") or ""),
    }

    canonical_job_summaries: list[dict[str, Any]] = []
    for job_dict in canonical_jobs:
        if not isinstance(job_dict, dict):
            continue
        canonical_job_summaries.append(
            {
                "job_id": str(job_dict.get("job_id") or ""),
                "session_id": str(job_dict.get("session_id") or ""),
                "status": str(job_dict.get("status") or ""),
                "final_outcome": str(job_dict.get("final_outcome") or ""),
            }
        )

    return {
        "phase2_payload_present": True,
        "canonical_session_summary": canonical_session_summary,
        "canonical_job_summaries": canonical_job_summaries,
        "typed_tool_summary": _phase2_manager_tool_summary(payload),
        "permission_decision_count": len(permission_decisions),
        "final_outcome": str(payload.get("final_outcome") or ""),
    }


# ------------------------------------------------------------------ #
# Bounded control-plane integration point                              #
# ------------------------------------------------------------------ #

def run_managed_job(job: Any, *, runtime: Any) -> dict[str, Any]:
    """Execute *job* on *runtime* and append ``phase2_manager_view``.

    This is the narrowest integration point that emits the runtime result
    payload. ``phase2_manager_view`` is appended additively; no legacy keys
    are removed or renamed.
    """
    payload: dict[str, Any] = runtime._execute_job(job)
    payload["phase2_manager_view"] = _phase2_manager_extract(payload)
    return payload


def _phase2_extract_typed_results(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract per-observation results from typed_tool_trace in *payload*.

    Returns one dict per tool_observation entry. tool_action entries are
    excluded. Returns [] if typed_tool_trace is absent, not a list, or empty.
    All field access is guarded; no exceptions escape.
    """
    try:
        trace = payload.get("typed_tool_trace")
    except Exception:
        return []
    if not isinstance(trace, list):
        return []
    results: list[dict[str, Any]] = []
    for entry in trace:
        try:
            if not isinstance(entry, dict):
                continue
            kind = str(entry.get("kind") or "")
            if kind == "tool_action":
                continue
            structured = entry.get("structured_payload")
            results.append(
                {
                    "tool_name": str(entry.get("tool_name") or entry.get("contract_name") or ""),
                    "status": str(entry.get("status") or ""),
                    "return_code": int(entry.get("return_code") or 0),
                    "stdout": str(entry.get("stdout") or ""),
                    "structured_payload": structured if isinstance(structured, dict) else {},
                    "duration_ms": int(entry.get("duration_ms") or 0),
                    "error": str(entry.get("error") or ""),
                }
            )
        except Exception:
            continue
    return results


def _phase2_manager_decision(manager_view: dict[str, Any]) -> dict[str, Any]:
    """Derive a deterministic operational signal from a phase2_manager_view dict.

    Returns a dict with keys: signal, reason, blocked_count,
    executed_count, tool_count, final_outcome.
    signal is one of: ok | all_tools_blocked | no_tools_ran |
    partial_block | phase2_absent.
    """
    if not manager_view.get("phase2_payload_present"):
        return {
            "signal": "phase2_absent",
            "reason": "phase2 payload not present in result",
            "blocked_count": 0,
            "executed_count": 0,
            "tool_count": 0,
            "final_outcome": str(manager_view.get("final_outcome") or ""),
        }
    tool_summary = manager_view.get("typed_tool_summary") or {}
    tool_count = int(tool_summary.get("tool_count") or 0)
    blocked_count = int(tool_summary.get("blocked_count") or 0)
    executed_count = int(tool_summary.get("executed_count") or 0)
    final_outcome = str(manager_view.get("final_outcome") or "")
    if tool_count == 0:
        signal, reason = "no_tools_ran", "no typed tool observations recorded"
    elif blocked_count > 0 and executed_count == 0:
        signal, reason = "all_tools_blocked", "all tool attempts were blocked by permission engine"
    elif blocked_count > 0 and executed_count > 0:
        signal, reason = "partial_block", "some tool attempts were blocked; some executed"
    else:
        signal, reason = "ok", "all observed tools executed without block"
    return {
        "signal": signal,
        "reason": reason,
        "blocked_count": blocked_count,
        "executed_count": executed_count,
        "tool_count": tool_count,
        "final_outcome": final_outcome,
    }


_DERIVE_TARGETS_LOW_VALUE_NAMES: frozenset[str] = frozenset(
    {"__init__.py", "setup.py", "conftest.py", "__main__.py"}
)


def _phase2_derive_read_targets(
    typed_results: list[dict[str, Any]],
    *,
    max_files: int = 3,
) -> list[dict[str, Any]]:
    """Convert SEARCH observation matches into READ_FILE argument specs.

    Returns up to *max_files* unique-path dicts ranked by specificity score.
    Score = match_frequency + framework/bin/tests bonus (+3) + compound-name bonus (+2)
            - low-value-name penalty (-5) - __pycache__ penalty (-10).
    Ties broken by path alphabetical order.
    Returns [] on any malformed or empty input without raising.
    """
    try:
        if not isinstance(typed_results, list):
            return []
        limit = max(1, int(max_files))
        freq: dict[str, int] = {}
        for entry in typed_results:
            try:
                if not isinstance(entry, dict):
                    continue
                if entry.get("tool_name") != "search":
                    continue
                if entry.get("status") != "executed":
                    continue
                matches = (entry.get("structured_payload") or {}).get("matches") or []
                for m in matches:
                    try:
                        path = str(m.get("path") or "").strip()
                        if path:
                            freq[path] = freq.get(path, 0) + 1
                    except Exception:
                        continue
            except Exception:
                continue
        if not freq:
            return []

        def _score(path: str) -> int:
            score = freq[path]
            p = Path(path)
            parts = p.parts
            name = p.name
            if any(part in ("framework", "bin", "tests") for part in parts):
                score += 3
            if "_" in p.stem:
                score += 2
            if name in _DERIVE_TARGETS_LOW_VALUE_NAMES:
                score -= 5
            if "__pycache__" in parts:
                score -= 10
            return score

        ranked = sorted(freq.keys(), key=lambda p: (-_score(p), p))
        selected = ranked[:limit]
        return [{"contract_name": "read_file", "arguments": {"path": p}} for p in selected]
    except Exception:
        return []


def _phase2_retrieval_summary(
    typed_results: list[dict[str, Any]],
    *,
    max_files: int = 3,
) -> dict[str, Any]:
    """Produce a compact deterministic summary of a retrieval run's typed results.

    All fields have safe defaults. No exceptions escape.
    """
    query = ""
    search_match_count = 0
    unique_file_paths: list[str] = []
    top_match_file = ""
    top_match_line = 0
    search_truncated = False
    repo_map_entry_count = 0
    repo_map_truncated = False

    freq: dict[str, int] = {}
    first_line: dict[str, int] = {}
    try:
        if not isinstance(typed_results, list):
            pass
        else:
            for entry in typed_results:
                try:
                    if not isinstance(entry, dict):
                        continue
                    tool = entry.get("tool_name")
                    status = entry.get("status")
                    sp = entry.get("structured_payload") or {}
                    if not isinstance(sp, dict):
                        sp = {}
                    if tool == "search" and status == "executed" and not query:
                        query = str(sp.get("query") or "")
                        search_match_count = int(sp.get("match_count") or 0)
                        search_truncated = bool(sp.get("matches_truncated_by_limit") or False)
                        matches = sp.get("matches") or []
                        for m in matches:
                            try:
                                p = str(m.get("path") or "").strip()
                                if p:
                                    freq[p] = freq.get(p, 0) + 1
                                    if p not in first_line:
                                        try:
                                            first_line[p] = int(m.get("line_number") or 0)
                                        except Exception:
                                            first_line[p] = 0
                            except Exception:
                                continue
                    elif tool == "repo_map" and status == "executed" and repo_map_entry_count == 0:
                        repo_map_entry_count = int(sp.get("entry_count") or 0)
                        repo_map_truncated = bool(sp.get("truncated") or False)
                except Exception:
                    continue
    except Exception:
        pass

    def _rs_score(path: str) -> int:
        score = freq.get(path, 0)
        p = Path(path)
        parts = p.parts
        name = p.name
        if any(part in ("framework", "bin", "tests") for part in parts):
            score += 3
        if "_" in p.stem:
            score += 2
        if name in _DERIVE_TARGETS_LOW_VALUE_NAMES:
            score -= 5
        if "__pycache__" in parts:
            score -= 10
        return score

    limit = max(1, int(max_files))
    ranked_paths = sorted(freq.keys(), key=lambda p: (-_rs_score(p), p))
    unique_file_paths = ranked_paths[:limit]
    top_match_file = unique_file_paths[0] if unique_file_paths else ""
    top_match_line = first_line.get(top_match_file, 0) if top_match_file else 0
    read_targets_derived = len(_phase2_derive_read_targets(typed_results, max_files=max_files))

    return {
        "query": query,
        "search_match_count": search_match_count,
        "unique_file_paths": unique_file_paths,
        "top_match_file": top_match_file,
        "top_match_line": top_match_line,
        "search_truncated": search_truncated,
        "repo_map_entry_count": repo_map_entry_count,
        "repo_map_truncated": repo_map_truncated,
        "read_targets_derived": read_targets_derived,
    }


def _phase3_extract_read_content(typed_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract READ_FILE observation content from typed_results.

    Returns one dict per executed read_file entry with path, stdout, size_bytes,
    structured_payload, duration_ms, error. Returns [] on empty or malformed input.
    All field access guarded; no exceptions escape.
    """
    try:
        if not isinstance(typed_results, list):
            return []
        out: list[dict[str, Any]] = []
        for entry in typed_results:
            try:
                if not isinstance(entry, dict):
                    continue
                tool = str(entry.get("tool_name") or entry.get("contract_name") or "")
                if tool != "read_file":
                    continue
                if entry.get("status") != "executed":
                    continue
                sp = entry.get("structured_payload")
                if not isinstance(sp, dict):
                    sp = {}
                stdout = str(entry.get("stdout") or "")
                path = str(sp.get("path") or entry.get("arguments", {}).get("path") or "")
                size_bytes = sp.get("size_bytes")
                if size_bytes is None:
                    size_bytes = len(stdout)
                else:
                    try:
                        size_bytes = int(size_bytes)
                    except Exception:
                        size_bytes = len(stdout)
                out.append({
                    "path": path,
                    "stdout": stdout,
                    "size_bytes": size_bytes,
                    "structured_payload": sp,
                    "duration_ms": int(entry.get("duration_ms") or 0),
                    "error": str(entry.get("error") or ""),
                })
            except Exception:
                continue
        return out
    except Exception:
        return []


def _phase3_read_content_summary(
    typed_results: list[dict[str, Any]],
    *,
    max_files: int = 3,
) -> dict[str, Any]:
    """Produce a compact summary of READ_FILE results from typed_results.

    All fields have safe zero-defaults; no exceptions escape.
    """
    try:
        entries = _phase3_extract_read_content(typed_results)
        files_read = len(entries)
        total_bytes = 0
        file_paths: list[str] = []
        seen: set[str] = set()
        top_file = ""
        top_file_bytes = 0
        any_errors = False
        limit = max(1, int(max_files))
        for e in entries:
            try:
                p = e.get("path") or ""
                if p and p not in seen:
                    seen.add(p)
                    if not top_file:
                        top_file = p
                        top_file_bytes = int(e.get("size_bytes") or 0)
                    if len(file_paths) < limit:
                        file_paths.append(p)
                total_bytes += int(e.get("size_bytes") or 0)
                if e.get("error"):
                    any_errors = True
            except Exception:
                continue
        return {
            "files_read": files_read,
            "file_paths": file_paths,
            "total_bytes": total_bytes,
            "top_file": top_file,
            "top_file_bytes": top_file_bytes,
            "any_errors": any_errors,
        }
    except Exception:
        return {
            "files_read": 0,
            "file_paths": [],
            "total_bytes": 0,
            "top_file": "",
            "top_file_bytes": 0,
            "any_errors": False,
        }


_RE_CLASS = re.compile(r"^class\s+(\w+)", re.MULTILINE)
_RE_DEF = re.compile(r"^def\s+(\w+)", re.MULTILINE)
_RE_METHOD = re.compile(r"^    def\s+(\w+)", re.MULTILINE)


def _phase3_extract_symbol_index(
    read_content_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Extract top-level class and function names from READ_FILE stdout.

    Input: list of read-content dicts (output of _phase3_extract_read_content).
    Returns one dict per valid input entry with path, classes, functions, symbol_count.
    Returns [] on non-list input. All field access guarded; no exceptions escape.
    """
    try:
        if not isinstance(read_content_results, list):
            return []
        out: list[dict[str, Any]] = []
        for entry in read_content_results:
            try:
                if not isinstance(entry, dict):
                    continue
                path = str(entry.get("path") or "")
                raw = entry.get("stdout")
                stdout = str(raw) if not isinstance(raw, str) else raw
                class_names: list[str] = []
                seen_classes: set[str] = set()
                for name in _RE_CLASS.findall(stdout):
                    if name not in seen_classes:
                        seen_classes.add(name)
                        class_names.append(name)
                func_names: list[str] = []
                seen_funcs: set[str] = set()
                for name in _RE_DEF.findall(stdout):
                    if name not in seen_funcs:
                        seen_funcs.add(name)
                        func_names.append(name)
                method_names: list[str] = []
                seen_methods: set[str] = set()
                for name in _RE_METHOD.findall(stdout):
                    if name not in seen_methods and name not in seen_funcs:
                        seen_methods.add(name)
                        method_names.append(name)
                out.append({
                    "path": path,
                    "classes": class_names,
                    "functions": func_names,
                    "methods": method_names,
                    "symbol_count": len(class_names) + len(func_names) + len(method_names),
                })
            except Exception:
                continue
        return out
    except Exception:
        return []


_SAFE_BUNDLE_DEFAULTS: dict[str, Any] = {
    "query": "",
    "total_files": 0,
    "total_symbols": 0,
    "total_content_chars": 0,
    "files_with_symbols": 0,
    "files": [],
    "top_file": "",
    "top_file_symbol_count": 0,
    "prompt_ready": False,
}


def _phase3_assemble_context_bundle(
    retrieval_summary: dict[str, Any],
    read_content_results: list[dict[str, Any]],
    symbol_index: list[dict[str, Any]],
) -> dict[str, Any]:
    """Join retrieval summary, read content, and symbol index into a context bundle.

    Returns a single structured dict suitable for injection into an inference prompt.
    All field access guarded; returns safe defaults on malformed input; no exceptions escape.
    """
    try:
        if not isinstance(retrieval_summary, dict):
            return dict(_SAFE_BUNDLE_DEFAULTS)
        if not isinstance(read_content_results, list):
            return dict(_SAFE_BUNDLE_DEFAULTS)
        if not isinstance(symbol_index, list):
            return dict(_SAFE_BUNDLE_DEFAULTS)

        query = str(retrieval_summary.get("query") or "")

        rc_lookup: dict[str, dict[str, Any]] = {}
        for rc in read_content_results:
            try:
                if not isinstance(rc, dict):
                    continue
                p = str(rc.get("path") or "")
                if p and p not in rc_lookup:
                    rc_lookup[p] = rc
            except Exception:
                continue

        files: list[dict[str, Any]] = []
        total_symbols = 0
        files_with_symbols = 0
        top_file = ""
        top_file_symbol_count = 0

        for entry in symbol_index:
            try:
                if not isinstance(entry, dict):
                    continue
                path = str(entry.get("path") or "")
                classes = list(entry.get("classes") or [])
                functions = list(entry.get("functions") or [])
                symbol_count = int(entry.get("symbol_count") or 0)

                rc_entry = rc_lookup.get(path) or {}
                size_bytes = int(rc_entry.get("size_bytes") or 0)
                raw_stdout = str(rc_entry.get("stdout") or "")
                stdout_excerpt = raw_stdout[:300].strip()

                files.append({
                    "path": path,
                    "classes": classes,
                    "functions": functions,
                    "symbol_count": symbol_count,
                    "size_bytes": size_bytes,
                    "stdout_excerpt": stdout_excerpt,
                })

                total_symbols += symbol_count
                if symbol_count > 0:
                    files_with_symbols += 1
                if symbol_count > top_file_symbol_count:
                    top_file_symbol_count = symbol_count
                    top_file = path
            except Exception:
                continue

        total_files = len(files)
        total_content_chars = sum(int(f.get("size_bytes") or 0) for f in files)
        prompt_ready = bool(
            query and total_files > 0 and (total_symbols > 0 or total_content_chars > 200)
        )

        return {
            "query": query,
            "total_files": total_files,
            "total_symbols": total_symbols,
            "total_content_chars": total_content_chars,
            "files_with_symbols": files_with_symbols,
            "files": files,
            "top_file": top_file,
            "top_file_symbol_count": top_file_symbol_count,
            "prompt_ready": prompt_ready,
        }
    except Exception:
        return dict(_SAFE_BUNDLE_DEFAULTS)


def _phase3_build_context_prompt(bundle: dict[str, Any]) -> str:
    """Convert a phase3_context_bundle into a formatted inference prompt string.

    Returns "" if bundle is not a dict, query is empty, or total_files is 0.
    All field access guarded; no exceptions escape.
    """
    try:
        if not isinstance(bundle, dict):
            return ""
        query = str(bundle.get("query") or "")
        total_files = int(bundle.get("total_files") or 0)
        if not query or total_files == 0:
            return ""
        top_file = str(bundle.get("top_file") or "")
        top_file_symbol_count = int(bundle.get("top_file_symbol_count") or 0)
        files = bundle.get("files") or []

        file_lines: list[str] = []
        all_classes: list[str] = []
        seen_classes: set[str] = set()
        all_functions: list[str] = []
        seen_functions: set[str] = set()

        for entry in files:
            try:
                if not isinstance(entry, dict):
                    continue
                p = str(entry.get("path") or "")
                sc = int(entry.get("symbol_count") or 0)
                file_lines.append(f"  {p} — {sc} symbol(s)")
                for c in (entry.get("classes") or []):
                    name = str(c)
                    if name and name not in seen_classes and len(all_classes) < 10:
                        seen_classes.add(name)
                        all_classes.append(name)
                for f in (entry.get("functions") or []):
                    name = str(f)
                    if name and name not in seen_functions and len(all_functions) < 10:
                        seen_functions.add(name)
                        all_functions.append(name)
            except Exception:
                continue

        classes_str = ", ".join(all_classes) if all_classes else "(none)"
        functions_str = ", ".join(all_functions) if all_functions else "(none)"
        files_block = "\n".join(file_lines) if file_lines else "  (none)"

        return (
            f'Retrieved {total_files} file(s) for query: "{query}"\n'
            f"\n"
            f"Files retrieved:\n"
            f"{files_block}\n"
            f"\n"
            f"Top file: {top_file} ({top_file_symbol_count} symbol(s))\n"
            f"\n"
            f"Key symbols across retrieved files:\n"
            f"  Classes: {classes_str}\n"
            f"  Functions: {functions_str}\n"
            f"\n"
            f"Task: Analyze the retrieved code context above. Identify the primary implementation "
            f"pattern, the entry point, and any non-obvious dependencies."
        )
    except Exception:
        return ""


_SAFE_INFERENCE_RESPONSE: dict[str, Any] = {
    "output_text": "",
    "backend": "",
    "inference_metadata": {},
    "output_chars": 0,
    "has_content": False,
}


def _phase3_extract_inference_response(
    result_payload: dict[str, Any],
) -> dict[str, Any]:
    """Extract inference output fields from a result payload dict.

    Returns a dict with output_text, backend, inference_metadata, output_chars, has_content.
    Returns safe defaults on any malformed input; no exceptions escape.
    """
    try:
        if not isinstance(result_payload, dict):
            return dict(_SAFE_INFERENCE_RESPONSE)
        output_text = str(result_payload.get("output") or "")
        backend = str(result_payload.get("backend") or "")
        im = result_payload.get("inference_metadata")
        inference_metadata = im if isinstance(im, dict) else {}
        output_chars = len(output_text)
        has_content = bool(output_text.strip())
        return {
            "output_text": output_text,
            "backend": backend,
            "inference_metadata": inference_metadata,
            "output_chars": output_chars,
            "has_content": has_content,
        }
    except Exception:
        return dict(_SAFE_INFERENCE_RESPONSE)


_SAFE_NEXT_ACTION: dict[str, Any] = {
    "action": "no_context",
    "reason": "derive_next_action_error",
    "context_adequate": False,
    "total_files": 0,
    "total_symbols": 0,
    "inference_has_content": False,
}


def _phase3_derive_next_action(
    context_bundle: dict[str, Any],
    inference_response: dict[str, Any],
) -> dict[str, Any]:
    """Derive a named action signal from phase3_context_bundle and phase3_inference_response.

    Returns one of four action tokens: no_context | insufficient_context | refine_retrieval | ready.
    All field access guarded; no exceptions escape.
    """
    try:
        try:
            total_files = int(context_bundle.get("total_files") or 0) if isinstance(context_bundle, dict) else 0
        except Exception:
            total_files = 0
        try:
            total_symbols = int(context_bundle.get("total_symbols") or 0) if isinstance(context_bundle, dict) else 0
        except Exception:
            total_symbols = 0
        try:
            inference_has_content = bool(inference_response.get("has_content")) if isinstance(inference_response, dict) else False
        except Exception:
            inference_has_content = False

        if not isinstance(context_bundle, dict) or not context_bundle.get("prompt_ready"):
            action = "no_context"
            reason = "context bundle not prompt-ready"
        elif not isinstance(inference_response, dict) or not inference_response.get("has_content"):
            action = "insufficient_context"
            reason = "inference produced no usable content"
        elif total_symbols == 0:
            action = "refine_retrieval"
            reason = "no symbols extracted from retrieved files; retrieval needs refinement"
        elif total_files == 0:
            action = "refine_retrieval"
            reason = "no files retrieved; retrieval needs refinement"
        else:
            action = "ready"
            reason = "context assembled with symbols; inference produced content"

        return {
            "action": action,
            "reason": reason,
            "context_adequate": action == "ready",
            "total_files": total_files,
            "total_symbols": total_symbols,
            "inference_has_content": inference_has_content,
        }
    except Exception:
        return dict(_SAFE_NEXT_ACTION)


_FOLLOWON_MAP: dict[str, str] = {
    "ready": "context_bundle_inference_probe",
    "insufficient_context": "read_after_retrieval",
    "refine_retrieval": "retrieval_probe",
    "no_context": "retrieval_probe",
}
_FOLLOWON_DEFAULT = "retrieval_probe"


def _phase3_select_followon_template(
    next_action: "dict[str, Any]",
    *,
    context_bundle: "dict[str, Any] | None" = None,
    retrieval_targets_exist: bool = False,
) -> str:
    """Map a phase3_next_action dict to a concrete follow-on template name.

    context_bundle and retrieval_targets_exist enable context-aware routing:
    - no_context + retrieval_targets_exist -> read_after_retrieval (targets ready to read)
    - insufficient_context + prompt_ready bundle -> context_bundle_inference_probe

    Safe default 'retrieval_probe' on any non-dict input, missing key, or unrecognized action.
    """
    try:
        if not isinstance(next_action, dict):
            return _FOLLOWON_DEFAULT
        action = str(next_action.get("action") or "")
        if action == "no_context":
            return "read_after_retrieval" if retrieval_targets_exist else _FOLLOWON_DEFAULT
        if action == "insufficient_context":
            bundle_prompt_ready = isinstance(context_bundle, dict) and bool(context_bundle.get("prompt_ready"))
            return "context_bundle_inference_probe" if bundle_prompt_ready else "read_after_retrieval"
        return _FOLLOWON_MAP.get(action, _FOLLOWON_DEFAULT)
    except Exception:
        return _FOLLOWON_DEFAULT


_SAFE_RECOMMENDATION: dict[str, Any] = {
    "query": "",
    "inference_text": "",
    "files_analyzed": 0,
    "symbol_count": 0,
    "top_file": "",
    "chars": 0,
    "recommendation_ready": False,
}


def _phase3_build_recommendation(
    context_bundle: "dict[str, Any]",
    inference_response: "dict[str, Any]",
) -> "dict[str, Any]":
    """Structure inference output into a named recommendation dict when action is 'ready'.

    Returns safe defaults dict on any exception or non-dict input. No exceptions escape.
    """
    try:
        if not isinstance(context_bundle, dict):
            return dict(_SAFE_RECOMMENDATION)
        if not isinstance(inference_response, dict):
            return dict(_SAFE_RECOMMENDATION)
        query = str(context_bundle.get("query") or "")
        inference_text = str(inference_response.get("output_text") or "")
        files_analyzed = int(context_bundle.get("total_files") or 0)
        symbol_count = int(context_bundle.get("total_symbols") or 0)
        top_file = str(context_bundle.get("top_file") or "")
        has_content = bool(inference_text.strip())
        recommendation_ready = bool(query and has_content)
        return {
            "query": query,
            "inference_text": inference_text,
            "files_analyzed": files_analyzed,
            "symbol_count": symbol_count,
            "top_file": top_file,
            "chars": len(inference_text),
            "recommendation_ready": recommendation_ready,
        }
    except Exception:
        return dict(_SAFE_RECOMMENDATION)


_SAFE_EDIT_PLAN: dict[str, Any] = {
    "query": "",
    "target_file": "",
    "plan_text": "",
    "has_replacement_format": False,
    "plan_ready": False,
    "chars": 0,
}


def _phase3_build_edit_plan(
    inference_response: "dict[str, Any]",
    recommendation: "dict[str, Any]",
) -> "dict[str, Any]":
    """Parse stage3_manager-format replacement instruction from edit-plan inference output.

    Returns safe defaults dict on any exception or non-dict input. No exceptions escape.
    """
    try:
        if not isinstance(inference_response, dict):
            return dict(_SAFE_EDIT_PLAN)
        if not isinstance(recommendation, dict):
            return dict(_SAFE_EDIT_PLAN)
        plan_text = str(inference_response.get("output_text") or "")
        target_file = str(recommendation.get("top_file") or "")
        query = str(recommendation.get("query") or "")
        has_replacement_format = bool(
            re.search(r"\S+::\s*replace exact text '.+' with '.+'", plan_text, re.DOTALL)
        )
        plan_ready = bool(plan_text.strip() and target_file)
        return {
            "query": query,
            "target_file": target_file,
            "plan_text": plan_text,
            "has_replacement_format": has_replacement_format,
            "plan_ready": plan_ready,
            "chars": len(plan_text),
        }
    except Exception:
        return dict(_SAFE_EDIT_PLAN)


_SAFE_EDIT_PLAN_VALIDATION: dict[str, Any] = {
    "old_text": "",
    "new_text": "",
    "target_file": "",
    "old_text_found": False,
    "validation_status": "not_validated",
    "preview_snippet": "",
    "executor_message": "",
}


def _phase3_validate_edit_plan(
    edit_plan: "dict[str, Any]",
    repo_root: "Any",
) -> "dict[str, Any]":
    """Validate the OLD text from an edit plan exists verbatim in its target file.

    Returns a dict with validation_status, old_text_found, preview_snippet, and
    executor_message (non-empty only when old_text_found is True). Read-only; never
    modifies the target file. No exceptions escape.
    """
    try:
        if not isinstance(edit_plan, dict):
            return dict(_SAFE_EDIT_PLAN_VALIDATION) | {"validation_status": "missing_inputs"}
        plan_text = str(edit_plan.get("plan_text") or "")
        target_file = str(edit_plan.get("target_file") or "")
        if not plan_text or not target_file:
            return dict(_SAFE_EDIT_PLAN_VALIDATION) | {"validation_status": "missing_inputs"}
        m = re.search(
            r"\S+::\s*replace exact text '(.+?)' with '(.+?)'",
            plan_text,
            re.DOTALL,
        )
        if not m:
            return dict(_SAFE_EDIT_PLAN_VALIDATION) | {
                "target_file": target_file,
                "validation_status": "no_replacement_format",
            }
        old_text = m.group(1)
        new_text = m.group(2)
        try:
            target_path = Path(str(repo_root)) / target_file
        except Exception:
            return dict(_SAFE_EDIT_PLAN_VALIDATION) | {
                "old_text": old_text,
                "new_text": new_text,
                "target_file": target_file,
                "validation_status": "target_file_missing",
            }
        if not target_path.exists():
            return {
                "old_text": old_text,
                "new_text": new_text,
                "target_file": target_file,
                "old_text_found": False,
                "validation_status": "target_file_missing",
                "preview_snippet": "",
                "executor_message": "",
            }
        try:
            file_content = target_path.read_text(encoding="utf-8")
        except Exception as _read_err:
            return {
                "old_text": old_text,
                "new_text": new_text,
                "target_file": target_file,
                "old_text_found": False,
                "validation_status": "read_error",
                "preview_snippet": "",
                "executor_message": "",
            }
        old_text_found = old_text in file_content
        if old_text_found:
            start_idx = file_content.index(old_text)
            preview_snippet = file_content[
                max(0, start_idx - 60): start_idx + len(old_text) + 60
            ].strip()
            executor_message = f"{target_file}:: replace exact text '{old_text}' with '{new_text}'"
            validation_status = "valid"
        else:
            preview_snippet = ""
            executor_message = ""
            validation_status = "old_text_not_found"
        return {
            "old_text": old_text,
            "new_text": new_text,
            "target_file": target_file,
            "old_text_found": old_text_found,
            "validation_status": validation_status,
            "preview_snippet": preview_snippet,
            "executor_message": executor_message,
        }
    except Exception:
        return dict(_SAFE_EDIT_PLAN_VALIDATION)


_SAFE_STAGE3_INVOCATION: dict[str, Any] = {
    "query": "",
    "target_file": "",
    "message": "",
    "commit_msg": "",
    "invocation_ready": False,
    "blocked_reason": "",
    "shell_command_preview": "",
}


def _phase3_build_stage3_manager_invocation(
    validation_result: "dict[str, Any]",
    edit_plan: "dict[str, Any]",
    recommendation: "dict[str, Any]",
) -> "dict[str, Any]":
    """Build a stage3_manager invocation spec from validated edit plan artifacts.

    invocation_ready is True only when validation_status=='valid' AND old_text_found==True.
    shell_command_preview is a fully-quoted shell command string; empty when not invocation_ready.
    No exceptions escape.
    """
    try:
        vr = validation_result if isinstance(validation_result, dict) else {}
        ep = edit_plan if isinstance(edit_plan, dict) else {}
        rec = recommendation if isinstance(recommendation, dict) else {}

        validation_status = str(vr.get("validation_status") or "")
        old_text_found = bool(vr.get("old_text_found"))
        target_file = str(vr.get("target_file") or ep.get("target_file") or "")
        message = str(vr.get("executor_message") or "")
        query = str(ep.get("query") or rec.get("query") or "")

        if validation_status == "valid" and old_text_found and target_file and message:
            invocation_ready = True
            blocked_reason = ""
        elif not target_file:
            invocation_ready = False
            blocked_reason = "no target_file"
        elif not message:
            invocation_ready = False
            blocked_reason = "no executor_message in validation_result"
        elif validation_status != "valid":
            invocation_ready = False
            blocked_reason = f"validation_status={validation_status!r} (must be 'valid')"
        elif not old_text_found:
            invocation_ready = False
            blocked_reason = "old_text_not_found in target file"
        else:
            invocation_ready = False
            blocked_reason = "unknown"

        safe_query = re.sub(r"[^a-zA-Z0-9 _-]", "", query)[:60].strip()
        commit_msg = f"phase3-edit: {safe_query}" if safe_query else "phase3-edit: apply edit plan"

        if invocation_ready:
            shell_command_preview = (
                f"python3 bin/stage3_manager.py"
                f" --query {shlex.quote(query)}"
                f" --target {shlex.quote(target_file)}"
                f" --message {shlex.quote(message)}"
                f" --commit-msg {shlex.quote(commit_msg)}"
            )
        else:
            shell_command_preview = ""

        return {
            "query": query,
            "target_file": target_file,
            "message": message,
            "commit_msg": commit_msg,
            "invocation_ready": invocation_ready,
            "blocked_reason": blocked_reason,
            "shell_command_preview": shell_command_preview,
        }
    except Exception:
        return dict(_SAFE_STAGE3_INVOCATION)


__all__ = [
    "_phase2_manager_present",
    "_phase2_manager_tool_summary",
    "_phase2_manager_extract",
    "_phase2_extract_typed_results",
    "_phase2_manager_decision",
    "_phase2_derive_read_targets",
    "_phase2_retrieval_summary",
    "_phase3_extract_read_content",
    "_phase3_read_content_summary",
    "_phase3_extract_symbol_index",
    "_phase3_assemble_context_bundle",
    "_phase3_build_context_prompt",
    "_phase3_extract_inference_response",
    "_phase3_derive_next_action",
    "_phase3_select_followon_template",
    "_phase3_build_recommendation",
    "_phase3_build_edit_plan",
    "_phase3_validate_edit_plan",
    "_phase3_build_stage3_manager_invocation",
    "run_managed_job",
]
