from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple
from pathlib import Path
import sys
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from domains.learning import LearningDomain


class ExecutorType(Enum):
    LOCAL_AIDER = "local_aider"
    CLAUDE_CHAT = "claude_chat"
    CLAUDE_CODE = "claude_code"


@dataclass
class TaskRoute:
    executor: ExecutorType
    model: str
    confidence: float
    reasoning: str


@dataclass
class PreflightResult:
    """Result of the Layer 2 pre-flight task shape validator."""
    ok: bool          # True = safe to proceed to Aider
    severity: str     # "block" | "warn" | "ok"
    reason: str       # human-readable explanation
    shape: str        # detected shape label e.g. "doc-append", "rewrite-large"


def preflight_validate(
    description: str,
    task_class: str,
    files: Optional[List[str]],
) -> PreflightResult:
    """
    Layer 2 pre-flight task shape validator (D-17-103).

    Called from aider-task.sh before Aider is invoked.
    Returns a PreflightResult; caller decides whether to block or warn.

    Operator override: AIDER_SKIP_PREFLIGHT=1 or --skip-preflight bypasses all checks.

    Heuristics (all approved by operator, 2026-05-04):

    BLOCK shapes:
      doc-append   — description has append/add/extend keywords + .md file >50 lines
                     (multi-paragraph doc authoring is Tier 2 per D-17-101)
      rewrite-large — description has rewrite/restructure/refactor + single file >300 lines
                     (today's qwen3-coder-next selective-rewrite failure shape)
      c1-multi-file — explicit C1 class + >2 files (violates Tier 1 doctrine)

    WARN shapes:
      long-doc-task — description >200 chars + .md file, no fix/update/correct keywords
                      (heuristic: operator is probably authoring, not patching)
    """
    import os
    if os.environ.get("AIDER_SKIP_PREFLIGHT") == "1":
        return PreflightResult(ok=True, severity="ok", reason="skipped (env override)", shape="none")

    desc_lower = description.lower()
    files = files or []

    # --- BLOCK: doc-append shape ---
    # D-17-101: multi-paragraph doc authoring permanently Tier 2.
    # An append to an existing .md file >50 lines is the failure shape.
    append_kws = ["append", "add section", "add §", "extend", "insert", "add finding",
                  "add chronicle", "add entry", "add related", "add step"]
    is_append_desc = any(kw in desc_lower for kw in append_kws)
    md_files_large = []
    for f in files:
        if f.endswith(".md"):
            try:
                p = Path(f)
                if p.exists():
                    line_count = len(p.read_text(errors="replace").splitlines())
                    if line_count > 50:
                        md_files_large.append((f, line_count))
            except OSError:
                pass
    if is_append_desc and md_files_large:
        names = ", ".join(f"{f} ({n} lines)" for f, n in md_files_large)
        return PreflightResult(
            ok=False,
            severity="block",
            reason=(
                f"doc-append shape detected: description has append/extend keywords "
                f"+ large .md file(s): {names}. "
                "Multi-paragraph doc authoring is Tier 2 (D-17-101). "
                "Use Claude Code instead. Override: --skip-preflight"
            ),
            shape="doc-append",
        )

    # --- BLOCK: rewrite-large shape ---
    # Today's qwen3-coder-next failure: selective rewrites of unrelated content on large files.
    rewrite_kws = ["rewrite", "restructure", "rework", "redesign"]
    is_rewrite = any(kw in desc_lower for kw in rewrite_kws)
    large_files = []
    for f in files:
        try:
            p = Path(f)
            if p.exists():
                lc = len(p.read_text(errors="replace").splitlines())
                if lc > 300:
                    large_files.append((f, lc))
        except OSError:
            pass
    if is_rewrite and large_files:
        names = ", ".join(f"{f} ({n} lines)" for f, n in large_files)
        return PreflightResult(
            ok=False,
            severity="block",
            reason=(
                f"rewrite-large shape: description contains rewrite/restructure keywords "
                f"+ large file(s): {names}. "
                "Risk of model selecting unrelated content to rewrite. "
                "Decompose into targeted hunks, or escalate to Tier 2. "
                "Override: --skip-preflight"
            ),
            shape="rewrite-large",
        )

    # --- BLOCK: C1 multi-file ---
    # Tier 1 doctrine: C1 tasks are single-source deliberate analysis; >2 files → Tier 2.
    if task_class == "C1" and len(files) > 2:
        return PreflightResult(
            ok=False,
            severity="block",
            reason=(
                f"C1 task with {len(files)} files exceeds Tier 1 limit (max 2 for C1). "
                "Escalate to Claude Code. Override: --skip-preflight"
            ),
            shape="c1-multi-file",
        )

    # --- WARN: long doc task ---
    # Heuristic: operator may be authoring new content on a doc file, which is Tier 2.
    fix_kws = ["fix", "update", "correct", "patch", "rename", "change", "replace", "remove"]
    is_fix = any(kw in desc_lower for kw in fix_kws)
    has_large_md = bool(md_files_large)  # reuse from above
    if len(description) > 200 and has_large_md and not is_fix:
        return PreflightResult(
            ok=True,
            severity="warn",
            reason=(
                f"long-doc-task: description is {len(description)} chars + large .md file. "
                "If this is multi-paragraph authoring, consider Tier 2 (Claude Code). "
                "Proceeding with Aider."
            ),
            shape="long-doc-task",
        )

    return PreflightResult(ok=True, severity="ok", reason="no unsafe shape detected", shape="none")


class TaskRouter:
    """Routes tasks to optimal executor based on classification and learning."""

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = repo_root or Path.cwd()
        try:
            self.learning = LearningDomain(self.repo_root)
        except Exception:
            self.learning = None

    def _infer_task_type(self, description: str, files: Optional[List[str]] = None) -> str:
        """Infer task type from description and context."""
        desc_lower = description.lower()

        if files:
            return "coding"
        if any(kw in desc_lower for kw in ["search", "find", "latest", "current", "what is"]):
            return "research"
        if any(kw in desc_lower for kw in ["architecture", "design", "plan", "strategy"]):
            return "architecture"

        return "general"

    def classify(self, description: str, files: Optional[List[str]] = None) -> TaskRoute:
        """Classify and route task using learning or keyword-based fallback."""
        task_type = self._infer_task_type(description, files)
        desc_lower = description.lower()

        # Try learning-based recommendation first
        if self.learning and task_type == "coding" and files:
            # Check if we have execution history for this task type
            task_types = self.learning.get_all_task_types()
            if "coding" in task_types:
                # Try LOCAL_AIDER first (most cost-effective)
                rec = self.learning.recommend_model("coding", "LOCAL_AIDER")
                if rec.confidence >= 0.6:
                    return TaskRoute(
                        ExecutorType.LOCAL_AIDER,
                        rec.model,
                        rec.confidence,
                        f"Learning-tuned: {rec.reason}",
                    )

                # Check if escalation is recommended
                should_escalate, escalation_reason = self.learning.should_escalate(
                    "coding"
                )
                if should_escalate:
                    rec = self.learning.recommend_model("coding", "CLAUDE_CODE")
                    return TaskRoute(
                        ExecutorType.CLAUDE_CODE,
                        rec.model,
                        rec.confidence,
                        f"Escalated: {escalation_reason}",
                    )

        # Keyword-based fallback routing
        # Research/current info
        # Coding tasks (file-bearing tasks route to LOCAL_AIDER first;
        # research/architecture keyword checks only fire when no files provided)
        if files:
            if len(files) == 1 and len(description) < 50:
                return TaskRoute(
                    ExecutorType.LOCAL_AIDER,
                    "qwen2.5-coder:7b",
                    0.95,
                    "Fast coding (1 file, <50 chars)",
                )
            elif len(files) <= 2 and len(description) < 100:
                return TaskRoute(
                    ExecutorType.LOCAL_AIDER,
                    "qwen2.5-coder:7b",
                    0.95,
                    "Simple coding",
                )
            elif len(files) <= 5:
                return TaskRoute(
                    ExecutorType.LOCAL_AIDER,
                    "qwen2.5-coder:14b",
                    0.9,
                    "Medium coding",
                )
            else:
                return TaskRoute(
                    ExecutorType.CLAUDE_CODE, "sonnet-4", 0.7, ">5 files - needs planning"
                )

        # Research/web (only when no files provided)
        if any(
            kw in desc_lower for kw in ["search", "find", "latest", "current", "what is"]
        ):
            return TaskRoute(
                ExecutorType.CLAUDE_CHAT, "sonnet-4", 0.9, "Requires web search"
            )

        # Architecture/design (only when no files provided — file-bearing edits
        # already routed above)
        if any(
            kw in desc_lower for kw in ["architecture", "design", "plan", "strategy"]
        ):
            return TaskRoute(
                ExecutorType.CLAUDE_CODE, "sonnet-4", 0.85, "Architectural work"
            )

        # Default
        return TaskRoute(
            ExecutorType.CLAUDE_CHAT, "sonnet-4", 0.6, "Ambiguous"
        )
