#!/usr/bin/env python3
"""Error pattern classification, solution database, rollback, and recovery learning.

Classifies errors into typed categories, selects a recovery strategy, attempts
execution with git rollback support, and updates a persistent success-rate
database so future recoveries benefit from past outcomes.
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ErrorPattern:
    """A registered error pattern with associated recovery strategy.

    Attributes:
        pattern_regex: Regular expression matched against error messages.
        error_type: Canonical error category (e.g. "syntax", "import").
        solution_strategy: Strategy name to apply for this error type.
        success_rate: Proportion of successful recoveries (0.0–1.0).
        examples: Sample error messages that match this pattern.
    """

    pattern_regex: str
    error_type: str
    solution_strategy: str
    success_rate: float = 0.0
    examples: List[str] = field(default_factory=list)


@dataclass
class RecoveryAttempt:
    """Record of a single recovery attempt.

    Attributes:
        error_msg: The original error message.
        error_type: Classified error type.
        strategy_used: Name of the strategy that was applied.
        success: Whether the recovery succeeded.
        git_sha_before: Git SHA at the time recovery was initiated.
        timestamp: ISO-format UTC timestamp.
    """

    error_msg: str
    error_type: str
    strategy_used: str
    success: bool
    git_sha_before: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# Default error patterns
# ---------------------------------------------------------------------------

_DEFAULT_PATTERNS: List[Dict[str, Any]] = [
    {
        "pattern_regex": r"SyntaxError|IndentationError|TabError",
        "error_type": "syntax",
        "solution_strategy": "fix_syntax",
        "success_rate": 0.75,
        "examples": ["SyntaxError: invalid syntax", "IndentationError: unexpected indent"],
    },
    {
        "pattern_regex": r"ModuleNotFoundError|ImportError|No module named",
        "error_type": "import",
        "solution_strategy": "install_missing",
        "success_rate": 0.65,
        "examples": ["ModuleNotFoundError: No module named 'requests'", "ImportError: cannot import name 'foo'"],
    },
    {
        "pattern_regex": r"TimeoutError|subprocess\.TimeoutExpired|timed out",
        "error_type": "timeout",
        "solution_strategy": "extend_timeout",
        "success_rate": 0.55,
        "examples": ["TimeoutError: timed out after 30s", "subprocess.TimeoutExpired"],
    },
    {
        "pattern_regex": r"PermissionError|Permission denied|Access is denied",
        "error_type": "permission",
        "solution_strategy": "rollback",
        "success_rate": 0.40,
        "examples": ["PermissionError: [Errno 13] Permission denied"],
    },
    {
        "pattern_regex": r"NameError|AttributeError|TypeError|ValueError|KeyError|IndexError",
        "error_type": "logic",
        "solution_strategy": "partial_save",
        "success_rate": 0.50,
        "examples": ["NameError: name 'x' is not defined", "AttributeError: 'NoneType' object has no attribute"],
    },
    {
        "pattern_regex": r"RecursionError|MemoryError|OverflowError",
        "error_type": "logic",
        "solution_strategy": "partial_save",
        "success_rate": 0.30,
        "examples": ["RecursionError: maximum recursion depth exceeded"],
    },
    {
        "pattern_regex": r"FileNotFoundError|No such file or directory",
        "error_type": "permission",
        "solution_strategy": "rollback",
        "success_rate": 0.45,
        "examples": ["FileNotFoundError: [Errno 2] No such file or directory"],
    },
]

# Mapping from error_type → strategy name
_STRATEGY_MAP: Dict[str, str] = {
    "syntax": "fix_syntax",
    "import": "install_missing",
    "timeout": "extend_timeout",
    "permission": "rollback",
    "logic": "partial_save",
    "unknown": "rollback",
}


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class RecoveryEngine:
    """Classify errors, select strategies, attempt recovery, and learn from outcomes.

    Loads and persists error pattern data to a JSON database so that
    success rates accumulate across sessions.

    Example::

        engine = RecoveryEngine(repo_root="/path/to/repo")
        attempt = engine.attempt_recovery("SyntaxError: unexpected token", context={})
        if attempt.success:
            print("Recovered!")
    """

    def __init__(
        self,
        repo_root: str,
        db_path: str = "artifacts/recovery_db.json",
    ) -> None:
        """Initialise and load the solution database.

        Args:
            repo_root: Absolute path to the repository root.
            db_path: Path (relative to repo_root, or absolute) to the JSON database.
        """
        self.repo_root = Path(repo_root)
        db = Path(db_path)
        self._db_path = db if db.is_absolute() else self.repo_root / db
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._patterns: List[ErrorPattern] = self._load_db()
        self._attempts: List[RecoveryAttempt] = []
        logger.debug("RecoveryEngine initialised db=%s patterns=%d", self._db_path, len(self._patterns))

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    def classify_error(self, error_msg: str) -> str:
        """Classify an error message into a canonical error type.

        Matches against registered patterns in order; falls back to "unknown".

        Args:
            error_msg: Raw error message string.

        Returns:
            Error type string: one of "syntax", "import", "timeout",
            "permission", "logic", or "unknown".
        """
        for pattern in self._patterns:
            if re.search(pattern.pattern_regex, error_msg, re.IGNORECASE):
                logger.debug("Classified error as %r via pattern %r", pattern.error_type, pattern.pattern_regex)
                return pattern.error_type
        return "unknown"

    def get_strategy(self, error_type: str, error_msg: str) -> str:  # pylint: disable=unused-argument
        """Return the recovery strategy for an error type.

        Args:
            error_type: Classified error type string.
            error_msg: Raw error message (reserved for future specialisation).

        Returns:
            Strategy name string.
        """
        # Check patterns for an exact type match (pattern may override default)
        for pattern in self._patterns:
            if pattern.error_type == error_type:
                return pattern.solution_strategy
        return _STRATEGY_MAP.get(error_type, "rollback")

    # ------------------------------------------------------------------
    # Recovery actions
    # ------------------------------------------------------------------

    def attempt_recovery(self, error_msg: str, context: Dict[str, Any]) -> RecoveryAttempt:
        """Classify an error, choose a strategy, and execute it.

        Records the attempt for learning purposes.

        Args:
            error_msg: The error message that triggered recovery.
            context: Optional context dict (may contain "file_path", "working_code").

        Returns:
            A ``RecoveryAttempt`` recording what was done and whether it succeeded.
        """
        sha = self._current_git_sha()
        error_type = self.classify_error(error_msg)
        strategy = self.get_strategy(error_type, error_msg)

        logger.info("Recovery: error_type=%s strategy=%s sha=%s", error_type, strategy, sha[:8] if sha else "?")

        success = self._apply_strategy(strategy, context, sha)

        attempt = RecoveryAttempt(
            error_msg=error_msg,
            error_type=error_type,
            strategy_used=strategy,
            success=success,
            git_sha_before=sha,
        )
        self._attempts.append(attempt)

        if success:
            self.learn_from_success(attempt)

        return attempt

    def rollback(self, sha: str) -> bool:
        """Roll back modified files to their state at a given git SHA.

        Uses ``git diff --name-only`` to identify changed files, then
        ``git checkout {sha} -- {files}`` to restore them.

        Args:
            sha: Git commit SHA to restore from.

        Returns:
            True if rollback succeeded, False otherwise.
        """
        if not sha:
            logger.warning("Rollback requested but SHA is empty")
            return False

        try:
            changed = subprocess.run(
                ["git", "diff", "--name-only", sha],
                capture_output=True,
                text=True,
                cwd=str(self.repo_root),
                timeout=30,
            )
            files = [f.strip() for f in changed.stdout.splitlines() if f.strip()]
            if not files:
                logger.info("Rollback: no changed files detected since %s", sha[:8])
                return True

            result = subprocess.run(
                ["git", "checkout", sha, "--"] + files,
                capture_output=True,
                text=True,
                cwd=str(self.repo_root),
                timeout=30,
            )
            if result.returncode == 0:
                logger.info("Rollback succeeded: %d files restored to %s", len(files), sha[:8])
                return True
            logger.error("Rollback failed: %s", result.stderr.strip())
            return False

        except subprocess.TimeoutExpired:
            logger.error("Rollback timed out")
            return False
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Rollback exception: %s", exc)
            return False

    def save_partial(self, working_code: str, file_path: str) -> bool:
        """Save the working portion of code to a partial-save file.

        Writes to ``{original_path}.partial`` to preserve progress without
        overwriting the original.

        Args:
            working_code: The code that is known to work.
            file_path: Intended final path (used to derive the partial path).

        Returns:
            True if saved successfully.
        """
        partial_path = Path(file_path).with_suffix(".partial")
        try:
            partial_path.write_text(working_code, encoding="utf-8")
            logger.info("Partial save: %d chars to %s", len(working_code), partial_path)
            return True
        except OSError as exc:
            logger.error("Partial save failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Learning
    # ------------------------------------------------------------------

    def learn_from_success(self, attempt: RecoveryAttempt) -> None:
        """Update success rates in the pattern database after a successful recovery.

        Uses an exponential moving average so recent successes matter more.

        Args:
            attempt: The successful recovery attempt.
        """
        for pattern in self._patterns:
            if pattern.error_type == attempt.error_type:
                # EMA: new_rate = 0.8 * old_rate + 0.2 * 1.0
                pattern.success_rate = round(0.8 * pattern.success_rate + 0.2, 4)
                logger.debug(
                    "Updated success_rate for %s → %.4f", pattern.error_type, pattern.success_rate
                )
        self._save_db()

    # ------------------------------------------------------------------
    # Database access
    # ------------------------------------------------------------------

    def get_solution_db(self) -> List[ErrorPattern]:
        """Return all registered error patterns.

        Returns:
            List of ``ErrorPattern`` instances.
        """
        return list(self._patterns)

    def add_pattern(self, pattern: ErrorPattern) -> None:
        """Register a new error pattern.

        Replaces an existing pattern with the same regex if found.

        Args:
            pattern: The pattern to add or update.
        """
        for i, existing in enumerate(self._patterns):
            if existing.pattern_regex == pattern.pattern_regex:
                self._patterns[i] = pattern
                self._save_db()
                return
        self._patterns.append(pattern)
        self._save_db()
        logger.debug("Added pattern: %s → %s", pattern.error_type, pattern.solution_strategy)

    def get_recovery_stats(self) -> Dict[str, Any]:
        """Return aggregated statistics about past recovery attempts.

        Returns:
            Dict with keys: success_rate_by_type, total_attempts, by_type_counts.
        """
        if not self._attempts:
            return {"success_rate_by_type": {}, "total_attempts": 0, "by_type_counts": {}}

        by_type: Dict[str, Dict[str, int]] = {}
        for attempt in self._attempts:
            et = attempt.error_type
            if et not in by_type:
                by_type[et] = {"total": 0, "success": 0}
            by_type[et]["total"] += 1
            if attempt.success:
                by_type[et]["success"] += 1

        rate_by_type = {
            et: round(v["success"] / v["total"], 3) if v["total"] else 0.0
            for et, v in by_type.items()
        }

        return {
            "success_rate_by_type": rate_by_type,
            "total_attempts": len(self._attempts),
            "by_type_counts": {et: v["total"] for et, v in by_type.items()},
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _apply_strategy(
        self, strategy: str, context: Dict[str, Any], sha: str
    ) -> bool:
        """Dispatch to the concrete strategy implementation.

        Args:
            strategy: Strategy name.
            context: Context dict; may contain "file_path" and "working_code".
            sha: Git SHA before the failure.

        Returns:
            True if the strategy reported success.
        """
        if strategy == "fix_syntax":
            # Syntax fixes are handled externally (e.g. by the code generator);
            # here we record intent and signal success so the caller retries.
            logger.info("Strategy fix_syntax: caller should re-generate the failing chunk")
            return True

        if strategy == "install_missing":
            # Extract module name from context or error message
            logger.info("Strategy install_missing: dependency resolution required")
            return False  # Requires human or pip intervention

        if strategy == "extend_timeout":
            logger.info("Strategy extend_timeout: signalling caller to retry with higher timeout")
            return True  # Caller responsible for actually extending

        if strategy == "rollback":
            return self.rollback(sha)

        if strategy == "partial_save":
            working_code = context.get("working_code", "")
            file_path = context.get("file_path", "/tmp/partial_save.py")
            if working_code:
                return self.save_partial(working_code, file_path)
            return False

        logger.warning("Unknown strategy: %s", strategy)
        return False

    def _current_git_sha(self) -> str:
        """Return the current HEAD git SHA.

        Returns:
            SHA string, or empty string on failure.
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=str(self.repo_root),
                timeout=10,
            )
            return result.stdout.strip()
        except Exception:  # pylint: disable=broad-except
            return ""

    def _load_db(self) -> List[ErrorPattern]:
        """Load error patterns from the JSON database file.

        Falls back to built-in defaults if the file is absent or corrupt.

        Returns:
            List of ``ErrorPattern`` instances.
        """
        if self._db_path.is_file():
            try:
                raw = json.loads(self._db_path.read_text(encoding="utf-8"))
                patterns = [ErrorPattern(**p) for p in raw]
                logger.debug("Loaded %d patterns from %s", len(patterns), self._db_path)
                return patterns
            except (json.JSONDecodeError, TypeError, KeyError) as exc:
                logger.warning("Failed to load recovery DB, using defaults: %s", exc)

        # Write defaults for next session
        defaults = [ErrorPattern(**p) for p in _DEFAULT_PATTERNS]
        self._db_path.write_text(json.dumps([asdict(p) for p in defaults], indent=2), encoding="utf-8")
        return defaults

    def _save_db(self) -> None:
        """Persist the current pattern list to disk."""
        try:
            self._db_path.write_text(
                json.dumps([asdict(p) for p in self._patterns], indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.error("Failed to persist recovery DB: %s", exc)
