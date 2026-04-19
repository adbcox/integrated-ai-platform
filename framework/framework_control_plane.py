"""Manager / control-plane helpers for consuming Phase 2 runtime payload.

All helpers are additive. No legacy keys are removed or renamed.
"""

from __future__ import annotations

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


def _phase2_derive_read_targets(
    typed_results: list[dict[str, Any]],
    *,
    max_files: int = 3,
) -> list[dict[str, Any]]:
    """Convert SEARCH observation matches into READ_FILE argument specs.

    Returns up to *max_files* unique-path dicts in first-occurrence order.
    Returns [] on any malformed or empty input without raising.
    """
    try:
        if not isinstance(typed_results, list):
            return []
        limit = max(1, int(max_files))
        seen: set[str] = set()
        targets: list[dict[str, Any]] = []
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
                        if not path or path in seen:
                            continue
                        seen.add(path)
                        targets.append({"contract_name": "read_file", "arguments": {"path": path}})
                        if len(targets) >= limit:
                            return targets
                    except Exception:
                        continue
            except Exception:
                continue
        return targets
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
                        seen: set[str] = set()
                        for m in matches:
                            try:
                                p = str(m.get("path") or "").strip()
                                if p and p not in seen:
                                    seen.add(p)
                                    if not top_match_file:
                                        top_match_file = p
                                        try:
                                            top_match_line = int(m.get("line_number") or 0)
                                        except Exception:
                                            top_match_line = 0
                                    unique_file_paths.append(p)
                            except Exception:
                                continue
                    elif tool == "repo_map" and status == "executed" and repo_map_entry_count == 0:
                        repo_map_entry_count = int(sp.get("entry_count") or 0)
                        repo_map_truncated = bool(sp.get("truncated") or False)
                except Exception:
                    continue
    except Exception:
        pass

    limit = max(1, int(max_files))
    unique_file_paths = unique_file_paths[:limit]
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
    "run_managed_job",
]
