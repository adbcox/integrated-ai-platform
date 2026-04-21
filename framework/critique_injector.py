"""Critique injection and retry guidance for the bounded coding loop.

Reads failure patterns from LocalMemoryStore and produces structured
critique text that can be injected into a retry prompt as extra_instructions
for render_prompt / PromptPack.render.

No outside-model dependency. Critique is generated deterministically from
local memory. Callers pass the critique string to render_prompt(extra_instructions=).

Import-time assertions guard all consumed local surfaces.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from framework.local_memory_store import FailurePattern, LocalMemoryStore, SuccessPattern
from framework.task_prompt_pack import SUPPORTED_TASK_CLASSES, render_prompt

# -- import-time interface assertions --
assert "task_kind" in FailurePattern.__dataclass_fields__, \
    "INTERFACE MISMATCH: FailurePattern.task_kind"
assert "error_type" in FailurePattern.__dataclass_fields__, \
    "INTERFACE MISMATCH: FailurePattern.error_type"
assert "error_summary" in FailurePattern.__dataclass_fields__, \
    "INTERFACE MISMATCH: FailurePattern.error_summary"
assert "old_string_prefix" in FailurePattern.__dataclass_fields__, \
    "INTERFACE MISMATCH: FailurePattern.old_string_prefix"
assert callable(render_prompt), \
    "INTERFACE MISMATCH: render_prompt not callable"


# Guidance text keyed by normalized error_type
_ERROR_GUIDANCE: dict[str, str] = {
    "old_string_not_found": (
        "The old_string was not found in the file. "
        "Verify that the exact bytes you intend to replace are present. "
        "Check for leading/trailing whitespace differences and line-ending variations."
    ),
    "permission_denied": (
        "The target path is outside the declared writable scope. "
        "Ensure the task target_file is within the allowed write directory."
    ),
    "test_failed": (
        "The patch was applied but the test suite failed. "
        "Review whether the change broke an invariant or introduced a syntax error. "
        "Consider a more minimal change that preserves existing behavior."
    ),
    "revert_failed": (
        "The revert step failed, leaving the file in an unknown state. "
        "Do not proceed with this file until the state is confirmed clean."
    ),
    "unsafe_task_kind": (
        "The task_kind is not in the safe task family. "
        "Use one of: text_replacement, helper_insertion, metadata_addition, bug_fix, narrow_test_update."
    ),
    "inspect_failed": (
        "The file could not be read. "
        "Confirm the target_file path is correct and the file exists."
    ),
    "unknown": (
        "An unexpected error occurred. "
        "Review the error detail and ensure the target file and strings are correct."
    ),
    "other": (
        "An unclassified error occurred. "
        "Review the full error detail before retrying."
    ),
}


@dataclass(frozen=True)
class CritiqueResult:
    task_kind: str
    error_type: str
    critique_text: str
    pattern_count: int
    retry_advised: bool

    def as_extra_instructions(self) -> str:
        """Return the critique formatted for use as render_prompt extra_instructions."""
        if not self.retry_advised:
            return (
                f"[RETRY BLOCKED]\n"
                f"This task class ({self.task_kind}) has a high recent failure rate "
                f"({self.pattern_count} failures). Do not retry without reviewing the "
                f"underlying cause.\n\n"
                f"Last error type: {self.error_type}\n"
                f"{self.critique_text}"
            )
        lines = [
            f"[RETRY GUIDANCE — error: {self.error_type}]",
            self.critique_text,
        ]
        if self.pattern_count > 1:
            lines.append(
                f"Note: this error type has occurred {self.pattern_count} time(s) "
                f"recently for this task class. Apply the guidance above carefully."
            )
        return "\n".join(lines)


def build_critique(
    *,
    task_kind: str,
    last_error: Optional[str],
    last_error_type: Optional[str] = None,
    memory_store: Optional[LocalMemoryStore] = None,
    max_failure_rate_for_retry: float = 0.8,
) -> CritiqueResult:
    """Build a CritiqueResult for a retry attempt.

    Args:
        task_kind: The task class being retried.
        last_error: The raw error string from the last attempt.
        last_error_type: If known, the classified error_type; otherwise derived.
        memory_store: LocalMemoryStore to query for historical patterns.
            If None, a default-path store is used (read-only query).
        max_failure_rate_for_retry: If the task's failure_rate exceeds this,
            retry_advised is False.
    """
    from framework.local_memory_store import _classify_error  # local import to avoid re-import cycle

    store = memory_store or LocalMemoryStore()
    error_type = last_error_type or _classify_error(last_error)
    guidance = _ERROR_GUIDANCE.get(error_type, _ERROR_GUIDANCE["other"])

    recent_failures = store.query_failures(task_kind=task_kind, error_type=error_type, limit=20)
    pattern_count = len(recent_failures)
    failure_rate = store.failure_rate(task_kind=task_kind)

    retry_advised = failure_rate <= max_failure_rate_for_retry

    if recent_failures:
        prior_samples = recent_failures[-3:]
        sample_lines = []
        for fp in prior_samples:
            sample_lines.append(
                f"  - [{fp.error_type}] in {fp.target_file_suffix}: "
                f"\"{fp.old_string_prefix[:40]}...\""
                if len(fp.old_string_prefix) > 40
                else f"  - [{fp.error_type}] in {fp.target_file_suffix}: \"{fp.old_string_prefix}\""
            )
        guidance = guidance + "\n\nRecent similar failures:\n" + "\n".join(sample_lines)

    return CritiqueResult(
        task_kind=task_kind,
        error_type=error_type,
        critique_text=guidance,
        pattern_count=pattern_count,
        retry_advised=retry_advised,
    )


def render_retry_prompt(
    task_kind: str,
    *,
    target_file: str,
    file_content: str,
    old_string: str,
    new_string_hint: str = "",
    context_snippet: str = "",
    last_error: Optional[str],
    memory_store: Optional[LocalMemoryStore] = None,
) -> str:
    """Build a full retry prompt with injected critique.

    Returns the rendered prompt string ready for GatewayRequest.prompt.
    Falls back to task_kind='text_replacement' pack if task_kind is unsupported.
    """
    safe_task_class = task_kind if task_kind in SUPPORTED_TASK_CLASSES else "text_replacement"
    critique = build_critique(
        task_kind=task_kind,
        last_error=last_error,
        memory_store=memory_store,
    )
    return render_prompt(
        safe_task_class,
        target_file=target_file,
        file_content=file_content,
        old_string=old_string,
        new_string_hint=new_string_hint,
        context_snippet=context_snippet,
        extra_instructions=critique.as_extra_instructions(),
    )


__all__ = [
    "CritiqueResult",
    "build_critique",
    "render_retry_prompt",
]
