#!/usr/bin/env python3
"""Review a specific commit with LLM."""

import sys
import argparse
import subprocess
import json
import re
from pathlib import Path
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from domains.coding import CodingDomain


def get_commit_diff(commit_hash: str, repo_root: Path) -> str:
    """Get diff for a commit."""
    try:
        result = subprocess.run(
            ["git", "diff", f"{commit_hash}^..{commit_hash}"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=repo_root,
        )
        return result.stdout
    except Exception as e:
        print(f"❌ Error getting diff: {e}", file=sys.stderr)
        return ""


def get_commit_message(commit_hash: str, repo_root: Path) -> str:
    """Get commit message."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%B", commit_hash],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=repo_root,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def review_commit(commit_hash: str, reviewer_model: str, repo_root: Path) -> Dict[str, Any]:
    """Review a commit using specified model."""
    print(f"📋 Retrieving commit info for {commit_hash[:8]}...")

    diff = get_commit_diff(commit_hash, repo_root)
    if not diff:
        return {
            "success": False,
            "error": "Could not get diff for commit",
            "issues": []
        }

    message = get_commit_message(commit_hash, repo_root)

    print(f"🔍 Reviewing with {reviewer_model}...")

    # Build review prompt
    review_prompt = f"""Review the following code changes.

Commit: {commit_hash[:8]}
Message: {message}

DIFF:
{diff[:5000]}

Analyze for:
1. Logic errors or bugs
2. Missing error handling
3. Security issues
4. Incomplete implementations
5. Code style issues
6. Performance problems

Respond with JSON:
{{
  "issues": [
    {{"severity": "low|medium|high", "category": "style|bug|security|logic|incomplete|performance", "description": "..."}}
  ],
  "summary": "Brief assessment",
  "overall_quality": "poor|fair|good|excellent"
}}
"""

    # Send to reviewer model
    cmd = [
        "aider",
        "--no-auto-commits",
        f"--model={reviewer_model}",
        "--read=/dev/stdin",
    ]

    try:
        proc = subprocess.run(
            cmd,
            input=review_prompt,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=repo_root,
        )

        output = proc.stdout + (proc.stderr or "")

        # Try to extract JSON
        try:
            json_match = re.search(r'\{.*"issues".*\}', output, re.DOTALL)
            if json_match:
                review_data = json.loads(json_match.group())
                return {
                    "success": True,
                    "commit": commit_hash[:8],
                    "message": message,
                    "issues": review_data.get("issues", []),
                    "summary": review_data.get("summary", ""),
                    "overall_quality": review_data.get("overall_quality", "fair"),
                }
        except Exception:
            pass

        return {
            "success": True,
            "commit": commit_hash[:8],
            "message": message,
            "issues": [],
            "summary": "No structured issues found",
            "output": output[:500],
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Review timeout",
            "issues": []
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "issues": []
        }


def print_review_report(result: Dict[str, Any]) -> None:
    """Print formatted review report."""
    if not result.get("success"):
        print(f"❌ Review failed: {result.get('error')}")
        return

    print(f"\n📊 Review Report: {result['commit']}")
    print(f"Message: {result['message']}")
    print(f"Quality: {result.get('overall_quality', 'unknown').upper()}")
    print()

    issues = result.get("issues", [])
    if not issues:
        print("✅ No issues found!")
        return

    print(f"Found {len(issues)} issue(s):\n")

    # Group by severity
    by_severity = {}
    for issue in issues:
        severity = issue.get("severity", "low")
        if severity not in by_severity:
            by_severity[severity] = []
        by_severity[severity].append(issue)

    # Print by severity order
    for severity in ["high", "medium", "low"]:
        if severity in by_severity:
            emoji = "🔴" if severity == "high" else "🟡" if severity == "medium" else "🟢"
            print(f"{emoji} {severity.upper()} ({len(by_severity[severity])} issues)")
            for issue in by_severity[severity]:
                print(f"   [{issue.get('category')}] {issue.get('description')}")
            print()

    print(f"Summary: {result.get('summary', '')}")


def main():
    parser = argparse.ArgumentParser(description="Review a git commit with LLM")
    parser.add_argument("commit", help="Commit hash to review")
    parser.add_argument(
        "--model",
        default="qwen2.5-coder:32b",
        help="Reviewer model (default: qwen2.5-coder:32b)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    repo_root = Path.cwd()

    # Validate commit exists
    try:
        subprocess.run(
            ["git", "cat-file", "-t", args.commit],
            capture_output=True,
            check=True,
            timeout=5,
            cwd=repo_root,
        )
    except Exception:
        print(f"❌ Commit not found: {args.commit}", file=sys.stderr)
        return 1

    # Run review
    result = review_commit(args.commit, args.model, repo_root)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_review_report(result)

    # Exit with error if issues found
    issues = result.get("issues", [])
    if issues:
        high_severity = any(i.get("severity") == "high" for i in issues)
        return 2 if high_severity else 1

    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
