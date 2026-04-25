#!/usr/bin/env python3
"""One-command setup: verify snippet library, optionally clone reference repos.

Usage:
    python3 bin/setup_references.py           # verify snippets only (fast)
    python3 bin/setup_references.py --clone   # also clone reference repos to ~/ai-reference/
    python3 bin/setup_references.py --report  # show what's available
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.reference_manager import ReferenceManager, REFERENCE_REPOS


def verify_snippets(mgr: ReferenceManager) -> bool:
    if not mgr.snippets_available():
        print(f"✗ Snippet library missing: {mgr.reference_dir}")
        print("  Expected: framework/patterns/*.py")
        return False

    snippets = sorted(mgr.reference_dir.glob("*.py"))
    total_chars = sum(s.stat().st_size for s in snippets)
    total_tokens = total_chars // 4
    print(f"✓ Snippet library: {len(snippets)} files, {total_chars:,} chars (~{total_tokens:,} tokens)")
    for s in snippets:
        print(f"  {s.name}")
    return True


def verify_repo_indexer() -> None:
    from framework.repo_indexer import RepoIndexer
    idx = RepoIndexer()
    repos = idx.list_repos()
    if not repos:
        print("○ Repo indexer: no repos cloned yet — run with --clone to enable smart context")
        return
    total_files = sum(c for _, c in repos)
    print(f"✓ Repo indexer: {len(repos)} repos, {total_files} .py files available")
    for name, count in repos:
        print(f"  ~/ai-reference/{name}: {count} files")


def verify_mini_context() -> bool:
    mini = REPO_ROOT / "artifacts" / "repo_context_mini.txt"
    if not mini.exists():
        print("✗ repo_context_mini.txt missing — run bin/build_context.py first")
        return False
    chars = mini.stat().st_size
    tokens = chars // 4
    print(f"✓ Mini context: {chars:,} chars (~{tokens:,} tokens)  [was 229k chars before fix]")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Set up aider reference code library")
    parser.add_argument("--clone", action="store_true", help="Clone reference repos to ~/ai-reference/")
    parser.add_argument("--report", action="store_true", help="Show detailed report")
    args = parser.parse_args()

    mgr = ReferenceManager(REPO_ROOT)

    print("\n── Reference System Setup ──────────────────────────────────────")

    ok = True
    ok = verify_snippets(mgr) and ok
    ok = verify_mini_context() and ok
    verify_repo_indexer()

    if args.clone:
        print(f"\n── Cloning reference repos to ~/ai-reference/ ──")
        print(f"  (Only small focused repos — NOT TheAlgorithms/Python which is 4GB)")
        results = mgr.clone_reference_repos()
        for name, success in results.items():
            status = "✓" if success else "✗"
            info = REFERENCE_REPOS[name]
            print(f"  {status} {name}: {info['description']}")

    if args.report or not args.clone:
        print()
        mgr.report()

    print("\n── Context Budget Summary (qwen2.5-coder:14b, 32k token window) ──")
    print("  Model context window: ~32,000 tokens  (131,072 chars @ chars/4)")
    print("  Aider system prompt:  ~2,000 tokens   (editblock coder)")
    print("  Mini repo context:    ~1,300 tokens   (was 57k — fixed)")
    print("  Curated patterns:     ~1,100 tokens   (2-3 pattern files)")
    print("  Task + target file:   ~1,000 tokens")
    print("  Repo files (smart):  up to 12,500 tokens  ← REFERENCE_BUDGET_CHARS=50k chars")
    print("  Remaining for output: ~14,000 tokens  (safe)")
    print()
    print("  Old cap (20k chars = 5k tokens) left 22k tokens unused.")
    print("  New cap (50k chars = 12.5k tokens) uses the budget properly.")

    if ok:
        print("\n✓ Reference system ready. Run:")
        print("  python3 bin/analyze_learning.py          # check training status")
        print("  python3 bin/auto_execute_roadmap.py --max-items 5  # run with references")
    else:
        print("\n✗ Setup incomplete. See errors above.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
