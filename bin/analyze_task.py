#!/usr/bin/env python3
"""Pre-flight task analyzer with interactive clarification."""

import sys
from pathlib import Path
from typing import List, Tuple, Optional
import subprocess

sys.path.insert(0, str(Path(__file__).parent.parent))

from domains.router import TaskRouter


class TaskAnalyzer:
    """Analyzes tasks and prompts for clarification before execution."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    def analyze(self, description: str, files: List[str]) -> Tuple[bool, List[str]]:
        """Analyze task and return (can_proceed, questions)."""
        questions = []

        # Check for file existence
        missing = [f for f in files if not (self.repo_root / f).exists()]
        if missing:
            questions.append(f"Files not found: {', '.join(missing)}. Did you mean a different path?")

        # Check for ambiguous scope
        scope_words = ["refactor", "redesign", "improve", "optimize", "enhance"]
        if any(word in description.lower() for word in scope_words) and len(files) == 1:
            questions.append(
                f"'{description}' sounds broad. Should this affect multiple files? Which specific function/class?"
            )

        # Check for missing details
        action_words = ["add", "update", "fix", "remove"]
        has_action = any(word in description.lower() for word in action_words)
        if not has_action and len(description.split()) < 5:
            questions.append(f"Task is vague: '{description}'. What specific change should be made?")

        # Search for similar past work
        similar = self._find_similar_commits(description)
        if similar:
            questions.append(f"Similar past work found:\n{similar}\nShould we follow the same pattern?")

        # Check if files are related
        if len(files) > 1:
            related = self._check_files_related(files)
            if not related:
                questions.append(f"Files seem unrelated: {', '.join(files)}. Is this one task or should it be split?")

        return len(questions) == 0, questions

    def _find_similar_commits(self, description: str) -> Optional[str]:
        """Search git history for similar work."""
        keywords = [w for w in description.lower().split() if len(w) > 4][:3]
        if not keywords:
            return None

        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "--all", "-20", "--grep", "|".join(keywords)],
                capture_output=True,
                text=True,
                cwd=self.repo_root,
                timeout=5,
            )
            commits = result.stdout.strip().split("\n")[:3]
            return "\n".join(f"  - {c}" for c in commits if c) if commits and commits[0] else None
        except Exception:
            return None

    def _check_files_related(self, files: List[str]) -> bool:
        """Check if files import each other or share common imports."""
        # Simple heuristic: same directory or common parent
        paths = [Path(f) for f in files]
        parents = [p.parent for p in paths]
        return len(set(parents)) == 1  # All in same directory


def interactive_prompt(questions: List[str]) -> bool:
    """Ask questions and get user confirmation."""
    print("\n⚠️  Pre-flight questions:\n")
    for i, q in enumerate(questions, 1):
        print(f"{i}. {q}\n")

    response = input("Continue anyway? (yes/no): ").strip().lower()
    return response in ["yes", "y"]


def main():
    if len(sys.argv) < 3:
        print("Usage: analyze_task.py 'description' file1 [file2...]")
        return 1

    description = sys.argv[1]
    files = sys.argv[2:]
    repo_root = Path(__file__).parent.parent

    # Route check
    router = TaskRouter(repo_root)
    route = router.classify(description, files)

    print(f"📊 Task Analysis")
    print(f"   Route: {route.executor.value}")
    print(f"   Confidence: {route.confidence:.0%}")
    print(f"   Reasoning: {route.reasoning}\n")

    # Analyze
    analyzer = TaskAnalyzer(repo_root)
    can_proceed, questions = analyzer.analyze(description, files)

    if can_proceed:
        print("✅ Task looks good - ready to execute")
        print(f"\nRun: ./bin/local_coding_task.py '{description}' {' '.join(files)}")
        return 0

    # Ask questions
    if interactive_prompt(questions):
        print("\n✅ Proceeding with task")
        print(f"\nRun: ./bin/local_coding_task.py '{description}' {' '.join(files)}")
        return 0
    else:
        print("\n❌ Task canceled - refine description and try again")
        return 1


if __name__ == "__main__":
    sys.exit(main())
