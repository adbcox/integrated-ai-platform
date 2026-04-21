"""Task-class prompt packs for local Ollama coding tasks.

Each pack provides a system prompt, a task template, and a render function
that fills in file context, old/new strings, and retrieval snippets to
produce a ready-to-use prompt for InferenceGateway.invoke.

No inference gateway imports — this module is prompt-string-only. Callers
build a GatewayRequest from the rendered string.

Supported task classes (aligned with MVPCodingLoopRunner.SAFE_TASK_KINDS plus
two additional narrow families):
  - text_replacement
  - helper_insertion
  - metadata_addition
  - bug_fix
  - narrow_test_update
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


SUPPORTED_TASK_CLASSES: frozenset = frozenset({
    "text_replacement",
    "helper_insertion",
    "metadata_addition",
    "bug_fix",
    "narrow_test_update",
})

_SYSTEM_BASE = (
    "You are a precise local coding assistant. "
    "Produce only the requested change. "
    "Do not add unrelated modifications. "
    "Do not add explanations unless asked. "
    "Output exactly the replacement text for the marked region."
)


@dataclass(frozen=True)
class PromptPack:
    task_class: str
    system_prompt: str
    task_template: str
    output_format: str

    def render(
        self,
        *,
        target_file: str,
        file_content: str,
        old_string: str = "",
        new_string_hint: str = "",
        context_snippet: str = "",
        extra_instructions: str = "",
    ) -> str:
        """Return a fully rendered prompt string."""
        parts: list[str] = [
            f"[SYSTEM]\n{self.system_prompt}",
            f"[TASK CLASS]\n{self.task_class}",
            f"[FILE]\n{target_file}",
        ]
        if context_snippet:
            parts.append(f"[CONTEXT]\n{context_snippet}")
        parts.append(f"[FILE CONTENT]\n{file_content}")
        task_body = self.task_template
        if old_string:
            task_body = task_body.replace("{{OLD_STRING}}", old_string)
        if new_string_hint:
            task_body = task_body.replace("{{NEW_STRING_HINT}}", new_string_hint)
        parts.append(f"[TASK]\n{task_body}")
        if extra_instructions:
            parts.append(f"[ADDITIONAL INSTRUCTIONS]\n{extra_instructions}")
        parts.append(f"[OUTPUT FORMAT]\n{self.output_format}")
        return "\n\n".join(parts)


_PACKS: dict[str, PromptPack] = {
    "text_replacement": PromptPack(
        task_class="text_replacement",
        system_prompt=_SYSTEM_BASE,
        task_template=(
            "Replace the following exact string in the file shown above:\n"
            "REPLACE:\n{{OLD_STRING}}\n\n"
            "WITH:\n{{NEW_STRING_HINT}}\n\n"
            "Return only the complete replacement text for the WITH block. "
            "Do not wrap in markdown code fences unless the content itself uses them."
        ),
        output_format=(
            "Return only the replacement text. "
            "No preamble. No explanation. No fences."
        ),
    ),
    "helper_insertion": PromptPack(
        task_class="helper_insertion",
        system_prompt=_SYSTEM_BASE,
        task_template=(
            "Insert a new helper into the file shown above.\n"
            "Insert after this anchor:\n{{OLD_STRING}}\n\n"
            "The helper should be a narrow, focused function or method. "
            "If a hint is provided:\n{{NEW_STRING_HINT}}\n\n"
            "Return only the complete new block to be inserted immediately after the anchor."
        ),
        output_format=(
            "Return only the inserted block (including the anchor line). "
            "No preamble. No explanation."
        ),
    ),
    "metadata_addition": PromptPack(
        task_class="metadata_addition",
        system_prompt=_SYSTEM_BASE,
        task_template=(
            "Add or update metadata in the file shown above.\n"
            "Target region:\n{{OLD_STRING}}\n\n"
            "Required change:\n{{NEW_STRING_HINT}}\n\n"
            "Metadata additions include: docstrings, module-level comments, "
            "__all__ entries, version strings, or reporting fields. "
            "Return only the complete replacement for the target region."
        ),
        output_format=(
            "Return only the replacement text for the target region. "
            "No preamble. No explanation."
        ),
    ),
    "bug_fix": PromptPack(
        task_class="bug_fix",
        system_prompt=(
            _SYSTEM_BASE + "\n"
            "For bug fixes: identify the minimal change that resolves the defect. "
            "Do not refactor surrounding code."
        ),
        task_template=(
            "Fix the bug in the region shown below from the file above.\n"
            "BUGGY REGION:\n{{OLD_STRING}}\n\n"
            "Bug description / fix hint:\n{{NEW_STRING_HINT}}\n\n"
            "Return only the corrected replacement for the buggy region. "
            "Change only what is necessary to fix the described defect."
        ),
        output_format=(
            "Return only the corrected replacement. "
            "No preamble. No explanation. Minimal change only."
        ),
    ),
    "narrow_test_update": PromptPack(
        task_class="narrow_test_update",
        system_prompt=(
            _SYSTEM_BASE + "\n"
            "For test updates: keep changes narrowly scoped to the named test or fixture. "
            "Do not modify unrelated tests."
        ),
        task_template=(
            "Update the test region shown below from the file above.\n"
            "CURRENT TEST REGION:\n{{OLD_STRING}}\n\n"
            "Required update:\n{{NEW_STRING_HINT}}\n\n"
            "Return only the complete replacement for this test region. "
            "Keep all other tests untouched."
        ),
        output_format=(
            "Return only the replacement test region. "
            "No preamble. No explanation."
        ),
    ),
}


def get_prompt_pack(task_class: str) -> PromptPack:
    """Return the PromptPack for a task class.

    Raises KeyError for unknown task classes.
    """
    if task_class not in _PACKS:
        raise KeyError(
            f"Unknown task_class {task_class!r}. "
            f"Supported: {sorted(SUPPORTED_TASK_CLASSES)}"
        )
    return _PACKS[task_class]


def render_prompt(
    task_class: str,
    *,
    target_file: str,
    file_content: str,
    old_string: str = "",
    new_string_hint: str = "",
    context_snippet: str = "",
    extra_instructions: str = "",
) -> str:
    """Convenience wrapper: get pack and render in one call."""
    pack = get_prompt_pack(task_class)
    return pack.render(
        target_file=target_file,
        file_content=file_content,
        old_string=old_string,
        new_string_hint=new_string_hint,
        context_snippet=context_snippet,
        extra_instructions=extra_instructions,
    )


__all__ = [
    "SUPPORTED_TASK_CLASSES",
    "PromptPack",
    "get_prompt_pack",
    "render_prompt",
]
