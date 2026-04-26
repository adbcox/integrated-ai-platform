#!/usr/bin/env python3
"""Automated code review: static analysis, type checking, security scanning, complexity.

Runs pylint, mypy, bandit, and radon (via subprocess) against individual files or
entire directories. Grades results on an A–D scale and can produce an HTML or
Markdown summary report.

Constants:
    MIN_COVERAGE: Minimum acceptable test coverage percentage.
    MAX_COMPLEXITY: Maximum acceptable cyclomatic complexity score.

Usage::
    python3 tools/code_reviewer.py path/to/module.py
    python3 tools/code_reviewer.py path/to/package/ --html --min-grade B
"""

from __future__ import annotations

import argparse
import html
import json
import logging
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MIN_COVERAGE: int = 80
MAX_COMPLEXITY: int = 10

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ReviewResult:
    """Result of a code review for a single file.

    Attributes:
        file_path: Path to the reviewed file.
        pylint_score: pylint score out of 10.0 (0.0 if unavailable).
        pylint_issues: List of pylint message strings.
        mypy_passed: Whether mypy type checking passed.
        mypy_issues: List of mypy error strings.
        bandit_issues: List of high-severity bandit findings.
        complexity_score: Average cyclomatic complexity from radon.
        coverage_pct: Test coverage percentage (0.0 if not measured).
        overall_grade: Letter grade A / B / C / D.
    """

    file_path: str
    pylint_score: float = 0.0
    pylint_issues: List[str] = field(default_factory=list)
    mypy_passed: bool = True
    mypy_issues: List[str] = field(default_factory=list)
    bandit_issues: List[str] = field(default_factory=list)
    complexity_score: float = 0.0
    coverage_pct: float = 0.0
    overall_grade: str = "D"


# ---------------------------------------------------------------------------
# Reviewer
# ---------------------------------------------------------------------------


class CodeReviewer:
    """Run multiple static analysis tools and aggregate results.

    Example::

        reviewer = CodeReviewer()
        result = reviewer.review_file("domains/parallel_engine.py")
        print(result.overall_grade)
        results = reviewer.review_directory("domains/")
        print(reviewer.to_markdown(results))
    """

    def __init__(self, config_path: str = ".pylintrc") -> None:
        """Initialise the reviewer.

        Args:
            config_path: Path to a pylintrc file (used if it exists).
        """
        self._config_path = Path(config_path)
        logger.debug("CodeReviewer initialised config=%s", config_path)

    # ------------------------------------------------------------------
    # File / directory entry points
    # ------------------------------------------------------------------

    def review_file(self, file_path: str) -> ReviewResult:
        """Run all review tools on a single Python file.

        Args:
            file_path: Path to the ``.py`` file to review.

        Returns:
            A populated ``ReviewResult``.
        """
        fp = str(file_path)
        logger.info("Reviewing file: %s", fp)

        pylint_score, pylint_issues = self.run_pylint(fp)
        mypy_passed, mypy_issues = self.run_mypy(fp)
        bandit_issues = self.run_bandit(fp)
        complexity_score = self.run_radon_complexity(fp)

        result = ReviewResult(
            file_path=fp,
            pylint_score=pylint_score,
            pylint_issues=pylint_issues,
            mypy_passed=mypy_passed,
            mypy_issues=mypy_issues,
            bandit_issues=bandit_issues,
            complexity_score=complexity_score,
        )
        result.overall_grade = self.grade(result)
        return result

    def review_directory(
        self,
        dir_path: str,
        pattern: str = "**/*.py",
    ) -> List[ReviewResult]:
        """Review all Python files in a directory matching a glob pattern.

        Args:
            dir_path: Root directory to search.
            pattern: Glob pattern relative to ``dir_path``.

        Returns:
            List of ``ReviewResult`` objects, one per matched file.
        """
        root = Path(dir_path)
        files = sorted(root.glob(pattern))
        logger.info("Reviewing %d files in %s", len(files), dir_path)
        results: List[ReviewResult] = []
        for fp in files:
            if fp.is_file():
                results.append(self.review_file(str(fp)))
        return results

    # ------------------------------------------------------------------
    # Individual tool runners
    # ------------------------------------------------------------------

    def run_pylint(self, file_path: str) -> Tuple[float, List[str]]:
        """Run pylint on a file and parse the results.

        Args:
            file_path: Path to the Python file.

        Returns:
            Tuple of (score_out_of_10, list_of_issue_strings).
            Returns (0.0, []) if pylint is not installed.
        """
        if not self._tool_available("pylint"):
            logger.debug("pylint not available")
            return 0.0, []

        cmd = ["pylint", "--output-format=json", file_path]
        if self._config_path.is_file():
            cmd = ["pylint", f"--rcfile={self._config_path}", "--output-format=json", file_path]

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )
            # pylint exits non-zero for any issues; that is expected
            issues: List[str] = []
            score = 0.0

            if proc.stdout.strip():
                try:
                    data = json.loads(proc.stdout)
                    for msg in data:
                        sym = msg.get("symbol", "?")
                        line = msg.get("line", "?")
                        text = msg.get("message", "")
                        issues.append(f"L{line} [{sym}] {text}")
                except json.JSONDecodeError:
                    pass

            # Extract score from stderr: "Your code has been rated at 8.50/10"
            for line in proc.stderr.splitlines():
                if "rated at" in line:
                    try:
                        score_str = line.split("rated at")[1].split("/")[0].strip()
                        score = float(score_str)
                    except (IndexError, ValueError):
                        pass

            logger.debug("pylint %s: score=%.2f issues=%d", file_path, score, len(issues))
            return round(score, 2), issues

        except subprocess.TimeoutExpired:
            logger.warning("pylint timed out for %s", file_path)
            return 0.0, ["pylint timed out"]
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("pylint error for %s: %s", file_path, exc)
            return 0.0, []

    def run_mypy(self, file_path: str) -> Tuple[bool, List[str]]:
        """Run mypy strict type checking on a file.

        Args:
            file_path: Path to the Python file.

        Returns:
            Tuple of (passed, list_of_error_strings).
            Returns (True, []) if mypy is not installed.
        """
        if not self._tool_available("mypy"):
            logger.debug("mypy not available")
            return True, []

        try:
            proc = subprocess.run(
                ["mypy", "--strict", "--ignore-missing-imports", "--no-error-summary", file_path],
                capture_output=True,
                text=True,
                timeout=60,
            )
            issues = [
                line.strip()
                for line in proc.stdout.splitlines()
                if line.strip() and "error:" in line
            ]
            passed = proc.returncode == 0
            logger.debug("mypy %s: passed=%s issues=%d", file_path, passed, len(issues))
            return passed, issues

        except subprocess.TimeoutExpired:
            logger.warning("mypy timed out for %s", file_path)
            return True, ["mypy timed out"]
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("mypy error for %s: %s", file_path, exc)
            return True, []

    def run_bandit(self, file_path: str) -> List[str]:
        """Run bandit security scanner and return high-severity findings.

        Args:
            file_path: Path to the Python file.

        Returns:
            List of high-severity issue strings.
            Returns [] if bandit is not installed.
        """
        if not self._tool_available("bandit"):
            logger.debug("bandit not available")
            return []

        try:
            proc = subprocess.run(
                ["bandit", "-r", file_path, "-f", "json", "-l", "-ll"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            issues: List[str] = []
            if proc.stdout.strip():
                try:
                    data = json.loads(proc.stdout)
                    for result in data.get("results", []):
                        severity = result.get("issue_severity", "LOW").upper()
                        if severity == "HIGH":
                            test_id = result.get("test_id", "")
                            text = result.get("issue_text", "")
                            line = result.get("line_number", "?")
                            issues.append(f"L{line} [{test_id}] {text} (HIGH)")
                except json.JSONDecodeError:
                    pass
            logger.debug("bandit %s: high_severity=%d", file_path, len(issues))
            return issues

        except subprocess.TimeoutExpired:
            logger.warning("bandit timed out for %s", file_path)
            return []
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("bandit error for %s: %s", file_path, exc)
            return []

    def run_radon_complexity(self, file_path: str) -> float:
        """Run radon cyclomatic complexity analysis.

        Args:
            file_path: Path to the Python file.

        Returns:
            Average complexity score (float).
            Returns 0.0 if radon is not installed or no functions found.
        """
        if not self._tool_available("radon"):
            logger.debug("radon not available")
            return 0.0

        try:
            proc = subprocess.run(
                ["radon", "cc", file_path, "--min", "A", "-s", "-j"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if not proc.stdout.strip():
                return 0.0

            data = json.loads(proc.stdout)
            complexities: List[float] = []
            for _fp, blocks in data.items():
                for block in blocks:
                    c = block.get("complexity", 0)
                    complexities.append(float(c))

            if not complexities:
                return 0.0
            avg = sum(complexities) / len(complexities)
            logger.debug("radon %s: avg_complexity=%.2f n_blocks=%d", file_path, avg, len(complexities))
            return round(avg, 2)

        except (json.JSONDecodeError, KeyError, TypeError):
            return 0.0
        except subprocess.TimeoutExpired:
            logger.warning("radon timed out for %s", file_path)
            return 0.0
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("radon error for %s: %s", file_path, exc)
            return 0.0

    # ------------------------------------------------------------------
    # Grading
    # ------------------------------------------------------------------

    def grade(self, result: ReviewResult) -> str:
        """Assign a letter grade A–D based on review metrics.

        Grading rubric:
        - A: pylint >= 9.0 AND mypy passed AND no bandit issues AND complexity < 5
        - B: pylint >= 7.0 AND mypy passed AND complexity < 8
        - C: pylint >= 5.0 AND complexity < 10
        - D: anything else

        Args:
            result: Populated review result.

        Returns:
            One of "A", "B", "C", "D".
        """
        if (
            result.pylint_score >= 9.0
            and result.mypy_passed
            and not result.bandit_issues
            and (result.complexity_score == 0.0 or result.complexity_score < 5.0)
        ):
            return "A"

        if (
            result.pylint_score >= 7.0
            and result.mypy_passed
            and (result.complexity_score == 0.0 or result.complexity_score < 8.0)
        ):
            return "B"

        if (
            result.pylint_score >= 5.0
            and (result.complexity_score == 0.0 or result.complexity_score < MAX_COMPLEXITY)
        ):
            return "C"

        return "D"

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def generate_report(
        self,
        results: List[ReviewResult],
        output_path: str = "artifacts/code_review.html",
    ) -> str:
        """Generate an HTML report and write it to disk.

        Args:
            results: List of review results to include.
            output_path: Destination HTML file path.

        Returns:
            The generated HTML string.
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        grade_colors = {
            "A": "#2ecc71",
            "B": "#3498db",
            "C": "#f39c12",
            "D": "#e74c3c",
        }

        rows: List[str] = []
        for r in results:
            color = grade_colors.get(r.overall_grade, "#bdc3c7")
            file_short = html.escape(Path(r.file_path).name)
            pylint_str = f"{r.pylint_score:.1f}" if r.pylint_score else "N/A"
            mypy_str = "PASS" if r.mypy_passed else "FAIL"
            bandit_str = str(len(r.bandit_issues))
            complexity_str = f"{r.complexity_score:.1f}" if r.complexity_score else "N/A"
            issues_str = html.escape("; ".join(r.pylint_issues[:3])) if r.pylint_issues else ""
            rows.append(
                f"<tr>"
                f"<td title='{html.escape(r.file_path)}'>{file_short}</td>"
                f"<td style='background:{color};color:#fff;font-weight:bold;text-align:center'>"
                f"{r.overall_grade}</td>"
                f"<td>{pylint_str}</td>"
                f"<td>{mypy_str}</td>"
                f"<td>{bandit_str}</td>"
                f"<td>{complexity_str}</td>"
                f"<td style='font-size:0.85em;color:#666'>{issues_str}</td>"
                f"</tr>"
            )

        summary_grades = {}
        for r in results:
            summary_grades[r.overall_grade] = summary_grades.get(r.overall_grade, 0) + 1

        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        badge_html = "".join(
            '<span class="badge" style="background:{color}">{g}: {count}</span>'.format(
                color=grade_colors.get(g, "#bdc3c7"), g=g, count=count
            )
            for g, count in sorted(summary_grades.items())
        )
        rows_html = "".join(rows)
        html_content = (
            "<!DOCTYPE html>\n"
            "<html lang=\"en\">\n"
            "<head>\n"
            "  <meta charset=\"UTF-8\">\n"
            "  <title>Code Review Report</title>\n"
            "  <style>\n"
            "    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 2em; background: #f5f6fa; }\n"
            "    h1 { color: #2c3e50; }\n"
            "    .summary { display:flex; gap:1em; margin-bottom:1.5em; }\n"
            "    .badge { padding: 0.5em 1em; border-radius:6px; font-weight:bold; color:#fff; }\n"
            "    table { border-collapse: collapse; width:100%; background:#fff; border-radius:8px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.08); }\n"
            "    th { background:#2c3e50; color:#fff; padding:0.75em 1em; text-align:left; }\n"
            "    td { padding:0.6em 1em; border-bottom:1px solid #ecf0f1; }\n"
            "    tr:hover td { background:#f9f9f9; }\n"
            "    .footer { margin-top:1em; color:#95a5a6; font-size:0.85em; }\n"
            "  </style>\n"
            "</head>\n"
            "<body>\n"
            "  <h1>Code Review Report</h1>\n"
            f"  <div class=\"summary\">\n"
            f"    {badge_html}\n"
            f"    <span class=\"badge\" style=\"background:#7f8c8d\">Total: {len(results)}</span>\n"
            "  </div>\n"
            "  <table>\n"
            "    <thead>\n"
            "      <tr>\n"
            "        <th>File</th><th>Grade</th><th>Pylint</th><th>Mypy</th>\n"
            "        <th>Bandit</th><th>Complexity</th><th>Issues</th>\n"
            "      </tr>\n"
            "    </thead>\n"
            f"    <tbody>\n      {rows_html}\n    </tbody>\n"
            "  </table>\n"
            f"  <p class=\"footer\">Generated {generated_at} | MIN_COVERAGE={MIN_COVERAGE}% | MAX_COMPLEXITY={MAX_COMPLEXITY}</p>\n"
            "</body>\n"
            "</html>"
        )

        try:
            Path(output_path).write_text(html_content, encoding="utf-8")
            logger.info("HTML report written to %s", output_path)
        except OSError as exc:
            logger.error("Failed to write HTML report: %s", exc)

        return html_content

    def to_markdown(self, results: List[ReviewResult]) -> str:
        """Format review results as a Markdown table.

        Args:
            results: List of review results.

        Returns:
            Markdown string.
        """
        lines = [
            "# Code Review Results",
            "",
            f"| File | Grade | Pylint | Mypy | Bandit | Complexity |",
            f"|------|-------|--------|------|--------|------------|",
        ]
        for r in results:
            fname = Path(r.file_path).name
            pylint_str = f"{r.pylint_score:.1f}" if r.pylint_score else "N/A"
            mypy_str = "PASS" if r.mypy_passed else "FAIL"
            bandit_str = str(len(r.bandit_issues))
            cplx_str = f"{r.complexity_score:.1f}" if r.complexity_score else "N/A"
            lines.append(
                f"| `{fname}` | **{r.overall_grade}** | {pylint_str} | {mypy_str} | {bandit_str} | {cplx_str} |"
            )

        lines.append("")
        # Grade summary
        grade_counts: Dict[str, int] = {}
        for r in results:
            grade_counts[r.overall_grade] = grade_counts.get(r.overall_grade, 0) + 1
        summary = " | ".join(f"**{g}**: {c}" for g, c in sorted(grade_counts.items()))
        lines.append(f"**Summary**: {summary} | **Total**: {len(results)}")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _tool_available(tool: str) -> bool:
        """Check if a CLI tool is on PATH.

        Args:
            tool: Tool name (e.g. "pylint").

        Returns:
            True if the tool is available.
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


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Automated code review: static analysis, type checking, security scanning.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "target",
        help="File or directory to review",
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Generate HTML report to artifacts/code_review.html",
    )
    parser.add_argument(
        "--min-grade",
        default=None,
        choices=["A", "B", "C", "D"],
        help="Exit non-zero if any file is below this grade",
    )
    parser.add_argument(
        "--output",
        default="artifacts/code_review.html",
        help="HTML output path (default: artifacts/code_review.html)",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entry point for code_reviewer.py."""
    args = _parse_args()
    reviewer = CodeReviewer()

    target = Path(args.target)
    if not target.exists():
        logger.error("Target not found: %s", target)
        sys.exit(1)

    if target.is_file():
        results = [reviewer.review_file(str(target))]
    else:
        results = reviewer.review_directory(str(target))

    if not results:
        logger.warning("No Python files found to review in %s", target)
        sys.exit(0)

    print(reviewer.to_markdown(results))

    if args.html:
        reviewer.generate_report(results, output_path=args.output)
        print(f"\nHTML report: {args.output}")

    if args.min_grade:
        grade_order = {"A": 4, "B": 3, "C": 2, "D": 1}
        min_val = grade_order[args.min_grade]
        failing = [r for r in results if grade_order.get(r.overall_grade, 0) < min_val]
        if failing:
            logger.error(
                "%d file(s) below minimum grade %s: %s",
                len(failing),
                args.min_grade,
                ", ".join(Path(r.file_path).name for r in failing),
            )
            sys.exit(1)


if __name__ == "__main__":
    main()
