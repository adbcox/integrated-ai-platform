"""Codebase symbol map and repomap generation for multi-file task planning.

This module provides structured understanding of repository topology, symbol definitions,
and inter-file dependencies to enable better multi-file code editing decisions.
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional, Set, Dict, List
from collections import defaultdict

from .compat import UTC


@dataclass(frozen=True)
class SymbolDef:
    """A symbol definition in a Python file."""
    name: str
    kind: str  # "class", "function", "variable", "import"
    line: int
    col_offset: int
    docstring: str = ""
    bases: list[str] = field(default_factory=list)  # For classes
    decorators: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class FileDependency:
    """File dependency information."""
    source_file: str
    target_file: str
    import_type: str  # "direct_import", "relative_import", "same_package"
    symbols_used: set[str] = field(default_factory=set)


@dataclass
class RepomapEntry:
    """Single file entry in the repository map."""
    path: str
    language: str  # "python", "shell", "text", "other"
    lines_of_code: int
    symbols: list[SymbolDef] = field(default_factory=list)
    dependencies: list[FileDependency] = field(default_factory=list)
    size_bytes: int = 0
    mtime_seconds: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "language": self.language,
            "lines_of_code": self.lines_of_code,
            "size_bytes": self.size_bytes,
            "mtime_seconds": self.mtime_seconds,
            "symbols": [
                {
                    "name": s.name,
                    "kind": s.kind,
                    "line": s.line,
                    "col_offset": s.col_offset,
                    "docstring": s.docstring,
                    "bases": s.bases,
                    "decorators": s.decorators,
                }
                for s in self.symbols
            ],
            "dependency_count": len(self.dependencies),
            "depends_on": [d.target_file for d in self.dependencies],
        }


class PythonSymbolExtractor(ast.NodeVisitor):
    """Extract symbol definitions from Python source."""

    def __init__(self, source_lines: list[str]) -> None:
        self.symbols: list[SymbolDef] = []
        self.source_lines = source_lines
        self._current_class: Optional[str] = None
        self._decorators: list[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        bases = [self._get_name_from_expr(b) for b in node.bases]
        docstring = ast.get_docstring(node) or ""
        self.symbols.append(
            SymbolDef(
                name=node.name,
                kind="class",
                line=node.lineno,
                col_offset=node.col_offset,
                docstring=docstring[:200],
                bases=bases,
                decorators=self._decorators.copy(),
            )
        )
        old_class = self._current_class
        self._current_class = node.name
        self._decorators = []
        self.generic_visit(node)
        self._current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        docstring = ast.get_docstring(node) or ""
        self.symbols.append(
            SymbolDef(
                name=node.name,
                kind="function",
                line=node.lineno,
                col_offset=node.col_offset,
                docstring=docstring[:200],
                decorators=self._decorators.copy(),
            )
        )
        self._decorators = []
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.symbols.append(
                    SymbolDef(
                        name=target.id,
                        kind="variable",
                        line=node.lineno,
                        col_offset=node.col_offset,
                    )
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for alias in node.names:
            name = alias.name
            self.symbols.append(
                SymbolDef(
                    name=name,
                    kind="import",
                    line=node.lineno,
                    col_offset=node.col_offset,
                    docstring=f"from {module}" if module else "import",
                )
            )
        self.generic_visit(node)

    def visit_Decorator(self, node: ast.expr) -> None:
        self._decorators.append(self._get_name_from_expr(node))

    def _get_name_from_expr(self, node: ast.expr) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name_from_expr(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_name_from_expr(node.func)
        return "unknown"


class RepomapGenerator:
    """Generate structured repository maps for multi-file understanding."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()
        self.entries: dict[str, RepomapEntry] = {}
        self._py_symbol_cache: dict[str, list[SymbolDef]] = {}

    def scan_repository(
        self,
        *,
        include_patterns: Optional[list[str]] = None,
        exclude_patterns: Optional[list[str]] = None,
        max_files: int = 1000,
    ) -> dict[str, RepomapEntry]:
        """Scan repo and extract symbols and dependencies."""

        include_patterns = include_patterns or ["**/*.py", "**/*.sh"]
        exclude_patterns = exclude_patterns or [".git/**", "__pycache__/**", "artifacts/**", ".venv/**"]

        py_files: list[Path] = []
        sh_files: list[Path] = []

        for pattern in include_patterns:
            if pattern.endswith(".py"):
                py_files.extend(self.repo_root.glob(pattern))
            elif pattern.endswith(".sh"):
                sh_files.extend(self.repo_root.glob(pattern))

        # Deduplicate and filter
        all_files = set()
        for f in py_files + sh_files:
            if len(all_files) >= max_files:
                break
            # Check exclusions
            skip = False
            for excl in exclude_patterns:
                if f.match(excl):
                    skip = True
                    break
            if not skip and f.is_file():
                all_files.add(f)

        # Process each file
        for file_path in sorted(all_files):
            self._process_file(file_path)

        # Extract dependencies
        for file_path in sorted(all_files):
            if file_path.suffix == ".py":
                self._extract_dependencies(file_path)

        return self.entries

    def _process_file(self, file_path: Path) -> None:
        rel_path = file_path.relative_to(self.repo_root).as_posix()

        try:
            content = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return

        size_bytes = file_path.stat().st_size
        mtime_seconds = int(file_path.stat().st_mtime)
        lines = content.split("\n")
        loc = len([l for l in lines if l.strip() and not l.strip().startswith("#")])

        language = self._detect_language(file_path)
        symbols: list[SymbolDef] = []

        if language == "python" and content.strip():
            symbols = self._extract_python_symbols(file_path, content)

        entry = RepomapEntry(
            path=rel_path,
            language=language,
            lines_of_code=loc,
            size_bytes=size_bytes,
            mtime_seconds=mtime_seconds,
            symbols=symbols,
        )
        self.entries[rel_path] = entry

    def _detect_language(self, file_path: Path) -> str:
        if file_path.suffix == ".py":
            return "python"
        elif file_path.suffix == ".sh":
            return "shell"
        return "text"

    def _extract_python_symbols(self, file_path: Path, content: str) -> list[SymbolDef]:
        if file_path in self._py_symbol_cache:
            return self._py_symbol_cache[file_path]

        try:
            tree = ast.parse(content)
            source_lines = content.split("\n")
            extractor = PythonSymbolExtractor(source_lines)
            extractor.visit(tree)
            symbols = extractor.symbols
        except SyntaxError:
            symbols = []

        self._py_symbol_cache[file_path] = symbols
        return symbols

    def _extract_dependencies(self, file_path: Path) -> None:
        rel_path = file_path.relative_to(self.repo_root).as_posix()
        if rel_path not in self.entries:
            return

        try:
            content = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return

        # Find import statements
        import_pattern = re.compile(
            r"^\s*(?:from\s+([\w.]+)\s+)?import\s+([\w,\s.]+)",
            re.MULTILINE
        )

        entry = self.entries[rel_path]
        dependencies_set: set[str] = set()

        for match in import_pattern.finditer(content):
            from_module = match.group(1)
            import_names = match.group(2)

            if from_module:
                # Resolve "from X import Y"
                target = self._resolve_import(rel_path, from_module)
                if target:
                    dependencies_set.add(target)
            elif import_names:
                # Resolve "import X"
                for name in import_names.split(","):
                    name = name.strip().split(".")[0]
                    target = self._resolve_import(rel_path, name)
                    if target:
                        dependencies_set.add(target)

        for dep_file in dependencies_set:
            if dep_file != rel_path and dep_file in self.entries:
                entry.dependencies.append(
                    FileDependency(
                        source_file=rel_path,
                        target_file=dep_file,
                        import_type="direct_import",
                        symbols_used=set(),
                    )
                )

    def _resolve_import(self, source_file: str, import_path: str) -> Optional[str]:
        """Try to resolve import statement to actual file."""
        parts = import_path.split(".")

        # Look for {import_path}.py
        candidate = "/".join(parts) + ".py"
        if candidate in self.entries:
            return candidate

        # Look for {import_path}/__init__.py
        candidate = "/".join(parts) + "/__init__.py"
        if candidate in self.entries:
            return candidate

        # Try relative imports
        source_dir = "/".join(source_file.split("/")[:-1])
        candidate = f"{source_dir}/{'/'.join(parts)}.py"
        if candidate in self.entries:
            return candidate

        return None

    def save_repomap(self, output_path: Path) -> None:
        """Save repomap to JSON artifact."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "schema_version": "repomap_v1",
            "generated_at_utc": dt.datetime.now(UTC).isoformat(timespec="seconds"),
            "repo_root": str(self.repo_root),
            "file_count": len(self.entries),
            "files": [entry.to_dict() for entry in self.entries.values()],
        }

        output_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


# Import datetime for timestamp
import datetime as dt
