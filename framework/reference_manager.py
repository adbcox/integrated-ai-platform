"""Reference code snippet manager for aider context injection.

Manages a curated library of small, focused code patterns that can be
injected as --read context into aider calls without overflowing the model's
context window.

Design constraints:
  - 7b model context: ~32k tokens. With task + files already using ~8k,
    reference budget is ~6k tokens max (~24k chars).
  - Never inject entire repos (TheAlgorithms/Python is gigabytes).
  - Curate specific pattern files: 50-200 lines each.

Usage:
    mgr = ReferenceManager(repo_root)
    flags = mgr.get_read_flags("MEDIA", used_chars=5000)
    # returns ["--read=/path/to/snippet.py", ...]

Setup:
    python3 bin/setup_references.py   # clone repos + extract snippets
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).parent.parent
# Snippets live in framework/patterns/ (versioned) not artifacts/ (gitignored)
REFERENCE_DIR = REPO_ROOT / "framework" / "patterns"

# Token budget: chars / 4 ≈ tokens. 7b model has 32k tokens.
# Subtract: system prompt (~500), task description (~200), target file (~500),
# mini repo context (~1300). Remaining for references: ~6000 tokens = ~24k chars.
REFERENCE_BUDGET_CHARS = 20_000  # conservative

# Category → ordered list of snippet paths (relative to REFERENCE_DIR).
# Earlier entries are higher priority when budget is tight.
CATEGORY_SNIPPETS: dict[str, list[str]] = {
    "MEDIA": [
        "patterns/observer_pattern.py",
        "patterns/pipeline_pattern.py",
        "patterns/adapter_pattern.py",
    ],
    "UI": [
        "patterns/facade_pattern.py",
        "patterns/component_pattern.py",
    ],
    "API": [
        "patterns/repository_pattern.py",
        "patterns/service_layer_pattern.py",
    ],
    "DATA": [
        "patterns/pipeline_pattern.py",
        "patterns/repository_pattern.py",
    ],
    "OPS": [
        "patterns/observer_pattern.py",
        "patterns/adapter_pattern.py",
    ],
    "LEARN": [
        "patterns/observer_pattern.py",
        "patterns/pipeline_pattern.py",
    ],
    "TEST": [
        "patterns/factory_pattern.py",
    ],
    "CORE": [
        "patterns/adapter_pattern.py",
        "patterns/factory_pattern.py",
    ],
    # Default for unknown categories
    "_default": [
        "patterns/adapter_pattern.py",
        "patterns/observer_pattern.py",
    ],
}

# Remote repos to clone for reference browsing (NOT injected directly into aider).
# Only small, focused repos. Avoid massive ones (TheAlgorithms = 4GB).
REFERENCE_REPOS = {
    "python-patterns": {
        "url": "https://github.com/faif/python-patterns",
        "description": "Pythonic implementations of common design patterns",
        "size_mb": 5,
    },
    "fastapi-realworld": {
        "url": "https://github.com/nsidnev/fastapi-realworld-example-app",
        "description": "Production FastAPI app structure",
        "size_mb": 2,
    },
}


class ReferenceManager:
    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = repo_root or REPO_ROOT
        self.reference_dir = self.repo_root / "framework" / "patterns"

    def snippets_available(self) -> bool:
        """True if the curated snippet library exists."""
        return self.reference_dir.exists() and any(self.reference_dir.glob("*.py"))

    def get_read_flags(
        self,
        category: str,
        used_chars: int = 0,
        budget_chars: int = REFERENCE_BUDGET_CHARS,
    ) -> list[str]:
        """Return --read flags for snippets that fit within the char budget.

        Args:
            category: Roadmap item category (MEDIA, UI, API, etc.)
            used_chars: Chars already consumed by other context (task, files, mini-context)
            budget_chars: Total char budget for all references

        Returns:
            List of "--read=/path/to/snippet.py" strings
        """
        if not self.snippets_available():
            return []

        remaining = budget_chars - used_chars
        if remaining <= 0:
            return []

        snippet_keys = CATEGORY_SNIPPETS.get(category.upper(), CATEGORY_SNIPPETS["_default"])
        flags: list[str] = []

        for rel_path in snippet_keys:
            # rel_path may be "patterns/observer_pattern.py" or just "observer_pattern.py"
            snippet = self.reference_dir / Path(rel_path).name
            if not snippet.exists():
                continue
            size = snippet.stat().st_size
            if size > remaining:
                break  # Ordered by priority, stop when budget exhausted
            flags.append(f"--read={snippet}")
            remaining -= size

        return flags

    def get_category_from_item_id(self, item_id: str) -> str:
        """Extract category from roadmap item ID like RM-MEDIA-001 → MEDIA."""
        parts = item_id.split("-")
        return parts[1] if len(parts) >= 3 else "_default"

    def clone_reference_repos(self, target_dir: Path | None = None) -> dict[str, bool]:
        """Clone reference repos for human browsing. Returns name → success map."""
        target = target_dir or (Path.home() / "ai-reference")
        target.mkdir(parents=True, exist_ok=True)
        results: dict[str, bool] = {}

        for name, info in REFERENCE_REPOS.items():
            dest = target / name
            if dest.exists():
                print(f"  {name}: already cloned, pulling...")
                r = subprocess.run(
                    ["git", "pull", "--ff-only"],
                    cwd=dest, capture_output=True, timeout=60,
                )
                results[name] = r.returncode == 0
            else:
                print(f"  {name}: cloning {info['url']} (~{info['size_mb']}MB)...")
                r = subprocess.run(
                    ["git", "clone", "--depth=1", info["url"], str(dest)],
                    capture_output=True, timeout=120,
                )
                results[name] = r.returncode == 0
                if not results[name]:
                    print(f"    FAILED: {r.stderr.decode()[:200]}")

        return results

    def generate_aider_conf(self, category: str, output_path: Path | None = None) -> Path:
        """Generate a .aider.conf.yml tuned for the given task category.

        This sets model-level options; reference files are injected dynamically
        at call time via --read flags rather than statically in the config.
        """
        conf_path = output_path or (self.repo_root / ".aider.conf.yml")
        read_flags = self.get_read_flags(category)

        lines = [
            "# Auto-generated by reference_manager.py — do not edit manually",
            f"# Category: {category}",
            "model: ollama/qwen2.5-coder:7b",
            "yes: true",
            "no-show-model-warnings: true",
            "no-auto-lint: true",
            "map-tokens: 0",
        ]

        if read_flags:
            lines.append("read:")
            for flag in read_flags:
                path = flag.replace("--read=", "")
                lines.append(f"  - {path}")

        conf_path.write_text("\n".join(lines) + "\n")
        return conf_path

    def report(self) -> None:
        """Print a summary of available reference snippets."""
        print(f"\nReference snippet library: {self.reference_dir}")
        if not self.snippets_available():
            print("  NOT SET UP — run: python3 bin/setup_references.py")
            return

        snippets = sorted(self.reference_dir.glob("*.py"))
        print(f"  {len(snippets)} snippets available:")
        for s in snippets:
            chars = s.stat().st_size
            tokens = chars // 4
            print(f"    {s.name:<35} {chars:6d} chars  ~{tokens:4d} tokens")

        print(f"\n  Budget: {REFERENCE_BUDGET_CHARS:,} chars total for references")
        print(f"  Category mappings:")
        for cat, paths in CATEGORY_SNIPPETS.items():
            if cat != "_default":
                print(f"    {cat:<10} → {', '.join(Path(p).stem for p in paths)}")
