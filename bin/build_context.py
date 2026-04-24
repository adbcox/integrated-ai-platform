#!/usr/bin/env python3
"""Build repository context for LLM awareness in Aider."""

import sys
import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

REPO_ROOT = Path(__file__).parent.parent
CONTEXT_FILE = REPO_ROOT / "artifacts" / "repo_context.txt"
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "artifacts", "venv", ".venv"}


def get_python_files() -> List[Path]:
    """Get all Python files in repo."""
    files = []
    for pyfile in REPO_ROOT.rglob("*.py"):
        # Skip hidden and cache dirs
        if any(skip in pyfile.parts for skip in SKIP_DIRS):
            continue
        files.append(pyfile)
    return sorted(files)


def extract_classes_and_functions(file_path: Path) -> List[Tuple[str, str]]:
    """Extract class and function signatures from Python file.

    Returns: [(name, signature), ...]
    """
    signatures = []
    try:
        with open(file_path) as f:
            tree = ast.parse(f.read())
    except (SyntaxError, UnicodeDecodeError):
        return []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            bases = ", ".join(
                (b.id if isinstance(b, ast.Name) else str(b)) for b in node.bases
            )
            bases_str = f"({bases})" if bases else ""
            signatures.append((node.name, f"class {node.name}{bases_str}"))

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
            args = ", ".join(arg.arg for arg in node.args.args)
            signatures.append((node.name, f"{prefix} {node.name}({args})"))

    return signatures


def extract_imports(file_path: Path) -> Set[str]:
    """Extract module imports from file."""
    imports = set()
    try:
        with open(file_path) as f:
            tree = ast.parse(f.read())
    except (SyntaxError, UnicodeDecodeError):
        return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])

    return imports


def get_file_docstring(file_path: Path) -> str:
    """Extract file-level docstring."""
    try:
        with open(file_path) as f:
            tree = ast.parse(f.read())
            docstring = ast.get_docstring(tree)
            if docstring:
                return docstring.split("\n")[0]
    except (SyntaxError, UnicodeDecodeError):
        pass
    return ""


def build_architecture_overview() -> str:
    """Build high-level architecture description."""
    return """REPOSITORY ARCHITECTURE
=======================

Core Domains:
- domains/coding.py: Code modification and Aider integration
- domains/learning.py: Execution metrics and model selection
- domains/router.py: Task classification and routing
- domains/home.py, domains/media.py: Service adapters (stubs)

Framework Layer:
- framework/: Job scheduling, worker runtime, execution abstractions
- framework/job_schema.py: Job definitions and lifecycle
- framework/code_executor.py: Executor abstraction (ClaudeCode, Aider)
- framework/worker_runtime.py: ParallelPool and job scheduling

CLI Tools:
- bin/local_coding_task.py: Single task executor with router
- bin/batch_coding_tasks.py: Batch task execution from file
- bin/generate_tests.py: Auto-generate tests after tasks
- bin/learning_insights.py: Query execution metrics
- bin/build_context.py: Generate repo context for LLMs
- bin/quick_task.sh: Fast task wrapper with auto-commit

Connectors:
- connectors/: External service adapters (arr_stack, home_assistant)
- connectors/__init__.py: Connector registry

Configuration:
- config/domains.yaml: Domain and service configuration

Key Patterns:
1. Domain Adapter Pattern: Service abstraction with config loading
2. Executor Abstraction: Swap between local Aider and Claude
3. Task Router: Classify tasks to optimal executor
4. Learning Loop: Record executions, tune model selection
5. CLI Composition: Small focused tools combining via shell/Python
"""


def build_domain_descriptions() -> str:
    """Build descriptions of each domain."""
    return """DOMAIN DESCRIPTIONS
====================

CodingDomain (domains/coding.py):
- execute_task(): Run code modification via Aider
- Model cascade: Try 14b, then 32b, then 7b on failure
- Git clean check: Validates working tree before execution
- Learning integration: Records success/failure to metrics
- Aider command building: Injects related files as context

LearningDomain (domains/learning.py):
- record_execution(): Log task outcomes to JSONL database
- get_success_rate(): Query model performance by task type
- recommend_model(): Suggest best model based on history
- should_escalate(): Detect when to use stronger executor
- get_failure_patterns(): Identify repeated error types

TaskRouter (domains/router.py):
- classify(): Map description+files to executor+model
- Learning-aware: Uses execution history when available
- Keyword fallback: Description analysis for cold start
- Confidence scoring: 0.0-1.0 based on history depth

Home/Media Domains:
- Connector adapters for external services
- Config-driven initialization
- Stub implementations ready for expansion
"""


def build_file_index(files: List[Path]) -> str:
    """Build index of all Python files with signatures."""
    output = ["FILE INDEX", "===========\n"]

    # Group by directory
    by_dir: Dict[str, List[Path]] = defaultdict(list)
    for f in files:
        rel_path = f.relative_to(REPO_ROOT)
        dir_name = rel_path.parent
        by_dir[str(dir_name)].append(f)

    for dir_name in sorted(by_dir.keys()):
        output.append(f"\n{dir_name}/")
        output.append("-" * (len(dir_name) + 1))

        for file_path in sorted(by_dir[dir_name]):
            rel_path = file_path.relative_to(REPO_ROOT)
            docstring = get_file_docstring(file_path)

            output.append(f"\n{rel_path.name}")
            if docstring:
                output.append(f"  {docstring}")

            # List classes and functions
            items = extract_classes_and_functions(file_path)
            if items:
                for name, sig in items[:10]:  # Limit to 10 per file
                    output.append(f"    {sig}")
                if len(items) > 10:
                    output.append(f"    ... and {len(items) - 10} more")

    return "\n".join(output)


def build_relationships() -> str:
    """Build import relationship graph."""
    output = ["IMPORT RELATIONSHIPS", "====================\n"]

    files = get_python_files()
    imports_by_file: Dict[str, Set[str]] = {}

    for file_path in files:
        rel_path = str(file_path.relative_to(REPO_ROOT))
        imports = extract_imports(file_path)
        imports_by_file[rel_path] = imports

    # Show key internal relationships
    output.append("Internal Dependencies:\n")

    internal_mods = {"domains", "framework", "connectors", "bin"}
    for file_path in sorted(files):
        rel_path = str(file_path.relative_to(REPO_ROOT))

        # Only show key files
        if not any(rel_path.startswith(mod) for mod in internal_mods):
            continue

        imports = imports_by_file.get(rel_path, set())
        if imports:
            output.append(f"{rel_path}")
            for imp in sorted(imports):
                if imp in {"domains", "framework", "connectors"}:
                    output.append(f"  ← {imp}.*")

    return "\n".join(output)


def build_patterns() -> str:
    """Build common patterns reference."""
    return """COMMON PATTERNS & CONVENTIONS
=============================

Task Execution Flow:
1. CLI tool (local_coding_task.py) parses args
2. TaskRouter classifies task to executor+model
3. If LOCAL_AIDER: CodingDomain.execute_task()
4. Aider runs with model cascade on failure
5. LearningDomain records outcome to metrics

Domain Pattern:
- __init__: Load config from YAML
- execute_task/execute_job: Main entry point
- _validate_*: Pre-flight checks
- submit_job: Framework integration

Learning Pattern:
- record_execution(): Called after task result
- Model selection uses recommendation(task_type, executor)
- Escalation triggered at <50% success rate
- Failure patterns tracked for debugging

Routing Pattern:
- Learning-based (if history available)
- Keyword-based fallback (cold start)
- Executor selection: cost-effectiveness -> capability
- Confidence scoring guides user decisions

Auto-commit Convention:
- Dirty trees auto-commit before task
- Message format: "WIP: {description[:60]}"
- --force flag skips git checks

Testing Convention:
- bin/generate_tests.py auto-generates pytest
- --auto-test flag triggers after success
- Runs locally before commit
"""


def main():
    """Build and write repo context."""
    print("📊 Building repository context...")

    files = get_python_files()
    print(f"   Found {len(files)} Python files")

    # Build sections
    sections = [
        ("OVERVIEW", build_architecture_overview()),
        ("DOMAINS", build_domain_descriptions()),
        ("FILE_INDEX", build_file_index(files)),
        ("RELATIONSHIPS", build_relationships()),
        ("PATTERNS", build_patterns()),
    ]

    # Write context file
    CONTEXT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(CONTEXT_FILE, "w") as f:
        f.write("REPOSITORY CONTEXT FOR LLM\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated from {len(files)} Python files\n")
        f.write("=" * 80 + "\n\n")

        for section_name, content in sections:
            f.write("\n" + ("=" * 80) + "\n")
            f.write(content)
            f.write("\n")

    size_kb = CONTEXT_FILE.stat().st_size / 1024
    print(f"✅ Context written: {CONTEXT_FILE} ({size_kb:.1f} KB)")
    print(f"   Sections: {', '.join(s[0] for s in sections)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
