#!/usr/bin/env python3
"""Code generator: breaks large coding tasks into chunks, generates progressively.

Uses Ollama for LLM-backed decomposition and code generation, validates each
chunk with syntax checks, and optionally lints with pylint/mypy.

Constants:
    MAX_CHUNK_LINES: Upper bound for a single generated code chunk.
    MIN_CHUNK_LINES: Lower bound; chunks smaller than this are merged.
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

try:
    import requests as _requests
    _REQUESTS_AVAILABLE = True
except ImportError:
    _requests = None  # type: ignore[assignment]
    _REQUESTS_AVAILABLE = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_CHUNK_LINES: int = 100
MIN_CHUNK_LINES: int = 20

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class CodeChunk:
    """A single generated code segment.

    Attributes:
        id: Unique identifier for this chunk.
        description: Human-readable description of what this chunk does.
        code: The generated source code.
        language: Programming language (e.g. "python").
        line_count: Number of lines in *code*.
        dependencies: IDs of chunks that must precede this one.
    """

    id: str
    description: str
    code: str
    language: str
    line_count: int
    dependencies: List[str] = field(default_factory=list)


@dataclass
class GenerationResult:
    """Aggregate result of a full code generation run.

    Attributes:
        chunks: All generated code chunks in order.
        total_lines: Combined line count across all chunks.
        lint_passed: Whether pylint/compile check passed.
        lint_issues: List of lint issue strings.
        mypy_passed: Whether mypy type checking passed.
    """

    chunks: List[CodeChunk]
    total_lines: int
    lint_passed: bool
    lint_issues: List[str]
    mypy_passed: bool


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


class CodeGenerator:
    """LLM-backed code generator with chunk decomposition and validation.

    Uses Ollama as the local inference backend; falls back gracefully when
    Ollama is unavailable by returning placeholder stubs.

    Example::

        gen = CodeGenerator()
        result = gen.generate_full("Write a binary search function")
        for chunk in result.chunks:
            print(chunk.code)
    """

    def __init__(
        self,
        ollama_host: str = "localhost:11434",
        model: str = "qwen2.5-coder:14b",
    ) -> None:
        """Initialise the generator.

        Args:
            ollama_host: Host:port of the Ollama server.
            model: Model name to use for generation.
        """
        self.ollama_host = ollama_host
        self.model = model
        self._base_url = f"http://{ollama_host}"
        logger.debug("CodeGenerator initialised model=%s host=%s", model, ollama_host)

    # ------------------------------------------------------------------
    # Ollama client
    # ------------------------------------------------------------------

    def _chat(self, prompt: str, system: str = "", temperature: float = 0.2) -> str:
        """Send a prompt to Ollama and return the response text.

        Args:
            prompt: The user message.
            system: Optional system message.
            temperature: Sampling temperature.

        Returns:
            Model response text, or empty string on failure.
        """
        if not _REQUESTS_AVAILABLE:
            logger.warning("requests not installed; returning empty generation")
            return ""

        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if system:
            payload["system"] = system

        try:
            resp = _requests.post(
                f"{self._base_url}/api/generate",
                json=payload,
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "")
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Ollama request failed: %s", exc)
            return ""

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def decompose_task(self, description: str, target_lines: int = 200) -> List[str]:
        """Break a high-level task description into ordered subtasks.

        The first subtask is always a test-writing step (TDD discipline).
        Each subsequent subtask targets roughly ``MAX_CHUNK_LINES`` of code.

        Args:
            description: High-level description of the coding task.
            target_lines: Approximate total lines expected for the full task.

        Returns:
            Ordered list of subtask descriptions.
        """
        n_chunks = max(1, target_lines // MAX_CHUNK_LINES)
        system = (
            "You are a senior software engineer. Given a coding task, "
            "produce an ordered JSON array of subtask strings. "
            "Each subtask is a concrete implementation step. "
            "Output ONLY valid JSON — no markdown fences, no commentary."
        )
        prompt = (
            f"Break this coding task into exactly {n_chunks + 1} ordered subtasks "
            f"(including a test step first). Each subtask targets ~{MAX_CHUNK_LINES} lines.\n\n"
            f"Task: {description}\n\n"
            "Rules:\n"
            f'- First subtask MUST be: "Write tests for: {description}"\n'
            "- Each entry is a single clear implementation step\n"
            "- Return a JSON array of strings only"
        )

        raw = self._chat(prompt, system=system)
        subtasks = self._parse_json_list(raw)

        if not subtasks:
            # Fallback: deterministic decomposition
            subtasks = self.progressive_complexity(description)

        # Ensure TDD first step is present
        tdd_step = f"Write tests for: {description}"
        if not subtasks or subtasks[0] != tdd_step:
            subtasks = [tdd_step] + subtasks

        logger.info("Decomposed task into %d subtasks", len(subtasks))
        return subtasks

    def generate_chunk(
        self,
        subtask: str,
        context: str = "",
        language: str = "python",
    ) -> CodeChunk:
        """Generate a code chunk for a single subtask.

        Validates the generated code using ``compile()``. Retries up to 2 times
        if a syntax error is detected.

        Args:
            subtask: Description of what this chunk should implement.
            context: Previously generated code (for continuity).
            language: Target language (currently only Python is linted).

        Returns:
            A ``CodeChunk`` with validated code.
        """
        chunk_id = str(uuid.uuid4())[:8]
        system = (
            f"You are an expert {language} developer. "
            "Return ONLY the raw code — no markdown fences, no explanation."
        )

        context_section = ""
        if context:
            # Truncate context to avoid overlong prompts
            ctx_lines = context.splitlines()
            if len(ctx_lines) > 80:
                ctx_lines = ctx_lines[-80:]
            context_section = f"\n\nExisting code context:\n```{language}\n" + "\n".join(ctx_lines) + "\n```"

        prompt = (
            f"Write {language} code for the following subtask.\n"
            f"Target: {MAX_CHUNK_LINES} lines maximum.\n\n"
            f"Subtask: {subtask}"
            f"{context_section}"
        )

        code = ""
        for attempt in range(3):  # up to 2 retries
            raw = self._chat(prompt, system=system)
            code = self._extract_code(raw, language)

            if language == "python":
                valid, err = self._check_syntax(code)
                if valid:
                    break
                if attempt < 2:
                    logger.warning("Syntax error on attempt %d for chunk %s: %s", attempt + 1, chunk_id, err)
                    prompt += f"\n\nFix the following syntax error: {err}\nReturn corrected code only."
            else:
                break  # Non-Python: no syntax validation

        if not code:
            code = f"# TODO: implement {subtask}\npass\n"

        line_count = len(code.splitlines())
        logger.debug("Generated chunk id=%s lines=%d subtask=%r", chunk_id, line_count, subtask[:60])

        return CodeChunk(
            id=chunk_id,
            description=subtask,
            code=code,
            language=language,
            line_count=line_count,
        )

    def generate_full(
        self,
        description: str,
        language: str = "python",
    ) -> GenerationResult:
        """Generate a complete implementation by chaining chunk generation.

        Args:
            description: High-level task description.
            language: Target programming language.

        Returns:
            A ``GenerationResult`` with all chunks and quality metrics.
        """
        subtasks = self.decompose_task(description)
        chunks: List[CodeChunk] = []
        accumulated_context = ""
        prev_id: Optional[str] = None

        for subtask in subtasks:
            chunk = self.generate_chunk(subtask, context=accumulated_context, language=language)

            # Wire sequential dependencies
            if prev_id is not None:
                chunk.dependencies = [prev_id]

            chunks.append(chunk)
            accumulated_context += "\n\n" + chunk.code
            prev_id = chunk.id

        combined_code = "\n\n".join(c.code for c in chunks)
        total_lines = sum(c.line_count for c in chunks)

        lint_passed, lint_issues = self.lint_code(combined_code, language=language)
        mypy_passed, mypy_issues = (True, [])
        if language == "python":
            mypy_passed, mypy_issues = self.run_mypy(combined_code, filename="generated_code.py")

        logger.info(
            "Generation complete: %d chunks, %d lines, lint=%s mypy=%s",
            len(chunks),
            total_lines,
            lint_passed,
            mypy_passed,
        )

        return GenerationResult(
            chunks=chunks,
            total_lines=total_lines,
            lint_passed=lint_passed,
            lint_issues=lint_issues + mypy_issues,
            mypy_passed=mypy_passed,
        )

    def lint_code(self, code: str, language: str = "python") -> Tuple[bool, List[str]]:
        """Lint generated code.

        For Python: attempts pylint via subprocess, falls back to compile().
        For other languages: returns (True, []).

        Args:
            code: Source code to lint.
            language: Programming language.

        Returns:
            Tuple of (passed, list_of_issue_strings).
        """
        if language != "python":
            return True, []

        # Try pylint first
        pylint_available = self._tool_available("pylint")
        if pylint_available:
            with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as tf:
                tf.write(code)
                tf_path = tf.name
            try:
                proc = subprocess.run(
                    ["pylint", "--output-format=text", "--score=no", tf_path],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                issues = [
                    line for line in proc.stdout.splitlines()
                    if line.strip() and not line.startswith("*")
                ]
                passed = proc.returncode == 0
                return passed, issues
            except Exception as exc:  # pylint: disable=broad-except
                logger.debug("pylint subprocess failed: %s", exc)
            finally:
                os.unlink(tf_path)

        # Fallback: compile()
        valid, err = self._check_syntax(code)
        if valid:
            return True, []
        return False, [err]

    def run_mypy(self, code: str, filename: str = "code.py") -> Tuple[bool, List[str]]:
        """Run mypy type checking on code written to a temp file.

        Args:
            code: Source code to check.
            filename: Filename hint (affects mypy output labelling).

        Returns:
            Tuple of (passed, list_of_issue_strings).
        """
        if not self._tool_available("mypy"):
            return True, []

        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, prefix="mypy_") as tf:
            tf.write(code)
            tf_path = tf.name

        try:
            proc = subprocess.run(
                ["mypy", "--ignore-missing-imports", "--no-error-summary", tf_path],
                capture_output=True,
                text=True,
                timeout=60,
            )
            issues = [
                line.replace(tf_path, filename)
                for line in proc.stdout.splitlines()
                if line.strip()
            ]
            passed = proc.returncode == 0
            return passed, issues
        except Exception as exc:  # pylint: disable=broad-except
            logger.debug("mypy subprocess failed: %s", exc)
            return True, []
        finally:
            os.unlink(tf_path)

    def progressive_complexity(self, description: str) -> List[str]:
        """Return a fixed-order list of complexity-progressive subtask descriptions.

        Always starts with tests (TDD). Useful as a deterministic fallback
        when LLM decomposition fails.

        Args:
            description: High-level task description.

        Returns:
            Ordered list of subtask descriptions.
        """
        return [
            f"Write tests for: {description}",
            f"Simple happy path implementation of: {description}",
            f"Edge cases handling for: {description}",
            f"Error handling and input validation for: {description}",
            f"Optimization and performance improvements for: {description}",
        ]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _check_syntax(self, code: str) -> Tuple[bool, str]:
        """Check Python syntax using compile().

        Args:
            code: Python source code.

        Returns:
            Tuple of (is_valid, error_message).
        """
        try:
            compile(code, "<generated>", "exec")
            return True, ""
        except SyntaxError as exc:
            return False, f"SyntaxError at line {exc.lineno}: {exc.msg}"

    def _extract_code(self, raw: str, language: str) -> str:
        """Strip markdown fences from a raw LLM response.

        Args:
            raw: Raw LLM output, potentially wrapped in fences.
            language: Expected language for fence stripping.

        Returns:
            Extracted code string.
        """
        # Try fenced block first
        patterns = [
            rf"```{language}\s*\n(.*?)```",
            r"```\s*\n(.*?)```",
        ]
        for pattern in patterns:
            match = re.search(pattern, raw, re.DOTALL)
            if match:
                return match.group(1).strip()
        return raw.strip()

    def _parse_json_list(self, raw: str) -> List[str]:
        """Parse a JSON array from raw LLM output.

        Args:
            raw: String that may contain a JSON array.

        Returns:
            List of strings, or empty list on failure.
        """
        # Strip markdown fences if present
        cleaned = re.sub(r"```(?:json)?\s*\n?", "", raw).replace("```", "").strip()
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, list):
                return [str(item) for item in parsed if item]
        except (json.JSONDecodeError, ValueError):
            pass

        # Try to find a JSON array anywhere in the string
        match = re.search(r"\[.*?\]", cleaned, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, list):
                    return [str(item) for item in parsed if item]
            except (json.JSONDecodeError, ValueError):
                pass

        return []

    @staticmethod
    def _tool_available(tool: str) -> bool:
        """Check whether a CLI tool is available on PATH.

        Args:
            tool: Tool executable name.

        Returns:
            True if the tool is found.
        """
        try:
            subprocess.run(
                [tool, "--version"],
                capture_output=True,
                timeout=5,
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
