#!/usr/bin/env python3
"""Conversational task interface with repo search and decomposition."""

import sys
import subprocess
from pathlib import Path
from typing import List, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from bin.search_repo import RepoSearch


class TaskChat:
    """Interactive task chat with repo awareness."""

    def __init__(self, repo_root: Path = None):
        self.repo_root = repo_root or Path.cwd()
        self.search = RepoSearch(self.repo_root)

    def search_related_files(self, query: str, limit: int = 5) -> List[Tuple[str, str]]:
        """Search repo for files related to task.

        Returns: [(file_path, context), ...]
        """
        results = self.search.search(query)
        files_seen = set()
        found = []

        for file_path, line_num, text, score in results[:20]:
            if file_path not in files_seen:
                found.append((file_path, text[:80]))
                files_seen.add(file_path)
                if len(found) >= limit:
                    break

        return found

    def suggest_decomposition(self, description: str, files: List[str]) -> List[str]:
        """Suggest how to decompose task into subtasks.

        Returns: List of suggested subtasks
        """
        # Simple heuristic-based decomposition
        desc_lower = description.lower()
        subtasks = []

        # Async pattern
        if "async" in desc_lower:
            subtasks.extend([
                "Add async/await to function signature",
                "Convert blocking calls to async",
                "Add task gathering for parallel execution",
            ])

        # API/connector pattern
        if any(kw in desc_lower for kw in ["api", "connector", "integration"]):
            subtasks.extend([
                "Define API client/connector class",
                "Implement health check method",
                "Add main execution method",
            ])

        # Testing pattern
        if any(kw in desc_lower for kw in ["test", "unit", "integration"]):
            subtasks.extend([
                "Write happy path test",
                "Write error case test",
                "Add edge case coverage",
            ])

        # Refactoring pattern
        if any(kw in desc_lower for kw in ["refactor", "rewrite", "redesign"]):
            subtasks.extend([
                "Analyze current structure",
                "Define target structure",
                "Implement new version",
                "Migrate callers",
            ])

        # Default: single step
        if not subtasks:
            subtasks = ["Complete the task as described"]

        return subtasks

    def interactive_task_flow(self) -> int:
        """Run interactive task flow."""
        print("🤖 Task Chat - Natural Language Task Decomposition")
        print("=" * 70)
        print("Describe what you want to build/fix/improve (no file paths needed)")
        print("Type 'quit' to exit\n")

        while True:
            # Get task description
            user_input = input("You: ").strip()

            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                return 0

            if not user_input:
                continue

            print()

            # Search related files
            print("🔍 Searching repository...")
            related_files = self.search_related_files(user_input, limit=5)

            if related_files:
                print("\nFound related files:")
                for file_path, context in related_files:
                    print(f"  📄 {file_path}")
                    print(f"     {context}")
            else:
                print("⚠️  No directly related files found")

            print()

            # Suggest decomposition
            print("💡 Suggested decomposition:")
            subtasks = self.suggest_decomposition(user_input, [f[0] for f in related_files])

            for i, subtask in enumerate(subtasks, 1):
                print(f"  {i}. {subtask}")

            print()

            # Ask for files to modify
            print("Which files should we modify? (comma-separated, or press Enter)")
            print("Suggestion: ", end="")
            suggested = ", ".join([f[0] for f in related_files[:3]])
            print(suggested if suggested else "(files will be auto-detected)")

            files_input = input("Files: ").strip()

            if files_input:
                files = [f.strip() for f in files_input.split(",")]
            elif related_files:
                files = [f[0] for f in related_files[:3]]
            else:
                print("❌ No files specified. Try again.\n")
                continue

            print()

            # Ask about subtask selection
            if len(subtasks) > 1:
                print("Which subtask to tackle first? (number, or 'all' for single commit)")
                choice = input("Choice [1]: ").strip() or "1"

                if choice.lower() == "all":
                    task_desc = user_input
                else:
                    try:
                        idx = int(choice) - 1
                        if 0 <= idx < len(subtasks):
                            task_desc = subtasks[idx]
                        else:
                            print("❌ Invalid choice\n")
                            continue
                    except ValueError:
                        print("❌ Please enter a number\n")
                        continue
            else:
                task_desc = user_input

            print()

            # Confirm and execute
            print(f"Task: {task_desc}")
            print(f"Files: {', '.join(files)}")
            confirm = input("Proceed? [y/n]: ").strip().lower()

            if confirm != "y":
                print("Cancelled.\n")
                continue

            print()
            print("=" * 70)

            # Execute via quick_task.sh
            try:
                result = subprocess.run(
                    ["bash", str(Path(__file__).parent / "quick_task.sh"), task_desc] + files,
                    cwd=self.repo_root,
                )

                if result.returncode == 0:
                    print("\n✅ Task completed!")
                else:
                    print(f"\n❌ Task failed with exit code {result.returncode}")
            except Exception as e:
                print(f"\n❌ Error: {e}")

            print()
            print("=" * 70)
            print()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Chat-based task interface with repo search"
    )
    parser.add_argument(
        "task",
        nargs="?",
        help="Task description (if not provided, starts interactive mode)",
    )
    parser.add_argument(
        "--files",
        default="",
        help="Files to modify (comma-separated)",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto-execute first suggestion without confirmation",
    )

    args = parser.parse_args()

    chat = TaskChat(Path.cwd())

    # Non-interactive mode with direct task
    if args.task:
        print(f"📝 Task: {args.task}")
        print()

        # Search files
        related = chat.search_related_files(args.task, limit=5)
        if related:
            print("Found related files:")
            for file_path, _ in related:
                print(f"  - {file_path}")

        # Get files
        if args.files:
            files = [f.strip() for f in args.files.split(",")]
        elif related:
            files = [f[0] for f in related[:3]]
        else:
            print("❌ No files found")
            return 1

        print()

        if args.auto:
            # Auto-execute
            print(f"Executing: {args.task}")
            print(f"Files: {', '.join(files)}\n")

            result = subprocess.run(
                ["bash", str(Path(__file__).parent / "quick_task.sh"), args.task] + files,
                cwd=chat.repo_root,
            )
            return result.returncode
        else:
            # Confirm
            confirm = input("Proceed? [y/n]: ").strip().lower()
            if confirm == "y":
                result = subprocess.run(
                    ["bash", str(Path(__file__).parent / "quick_task.sh"), args.task] + files,
                    cwd=chat.repo_root,
                )
                return result.returncode
            else:
                print("Cancelled.")
                return 0

    # Interactive mode
    return chat.interactive_task_flow()


if __name__ == "__main__":
    sys.exit(main())
