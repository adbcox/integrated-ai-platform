"""tests/unit/test_dependency_analyzer.py

Unit tests for domains/dependency_analyzer.py.

All tests use tmp_path to create temporary .md files and are fully isolated
from the filesystem — no shared state between tests.
"""
from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent
from typing import List

import pytest

# ── Import guard ──────────────────────────────────────────────────────────────
try:
    from domains.dependency_analyzer import DependencyAnalyzer  # type: ignore
    _ANALYZER_AVAILABLE = True
except ImportError:
    _ANALYZER_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not _ANALYZER_AVAILABLE,
    reason="domains.dependency_analyzer not yet implemented",
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def _write_item(
    items_dir: Path,
    item_id: str,
    title: str,
    status: str = "backlog",
    deps: List[str] | None = None,
) -> Path:
    """Write a minimal roadmap .md file and return its path."""
    deps_str = ""
    if deps:
        dep_lines = "\n".join(f"- {d}" for d in deps)
        deps_str = f"\n## Dependencies\n{dep_lines}"

    content = dedent(f"""\
        # {item_id}: {title}

        **Status**: {status}
        **Category**: Testing
        **Priority**: Medium
        **LOE**: S
        **Strategic Value**: 5
        {deps_str}
        """)
    p = items_dir / f"{item_id}.md"
    p.write_text(content)
    return p


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestLoadItemsParseDependencies:
    @pytest.mark.unit
    def test_load_items_parses_dependencies(self, tmp_path: Path) -> None:
        """Items directory with dep sections should yield parsed dependency lists."""
        items_dir = tmp_path / "ITEMS"
        items_dir.mkdir()
        _write_item(items_dir, "A", "Alpha", deps=["B", "C"])
        _write_item(items_dir, "B", "Beta")
        _write_item(items_dir, "C", "Gamma")

        analyzer = DependencyAnalyzer(items_dir=str(items_dir))
        items = analyzer.load_items()

        item_a = next((i for i in items if i["id"] == "A"), None)
        assert item_a is not None, "Item A should be loaded"
        assert "B" in item_a.get("dependencies", [])
        assert "C" in item_a.get("dependencies", [])

    @pytest.mark.unit
    def test_empty_graph(self, tmp_path: Path) -> None:
        """An empty items directory should return an empty list without raising."""
        items_dir = tmp_path / "ITEMS"
        items_dir.mkdir()

        analyzer = DependencyAnalyzer(items_dir=str(items_dir))
        items = analyzer.load_items()

        assert isinstance(items, list)
        assert len(items) == 0


class TestCircularDependencies:
    @pytest.mark.unit
    def test_find_circular_deps(self, tmp_path: Path) -> None:
        """A→B→C→A cycle should be detected and reported."""
        items_dir = tmp_path / "ITEMS"
        items_dir.mkdir()
        _write_item(items_dir, "A", "Alpha", deps=["B"])
        _write_item(items_dir, "B", "Beta",  deps=["C"])
        _write_item(items_dir, "C", "Gamma", deps=["A"])

        analyzer = DependencyAnalyzer(items_dir=str(items_dir))
        analyzer.load_items()
        cycles = analyzer.find_circular_deps()

        assert len(cycles) >= 1, "Should detect at least one cycle"
        # Cycle should include all three nodes in some order
        all_cycle_nodes = {node for cycle in cycles for node in cycle}
        assert all_cycle_nodes >= {"A", "B", "C"}

    @pytest.mark.unit
    def test_no_cycle_in_dag(self, tmp_path: Path) -> None:
        """A clean DAG (A→B→C) should produce zero cycles."""
        items_dir = tmp_path / "ITEMS"
        items_dir.mkdir()
        _write_item(items_dir, "A", "Alpha", deps=["B"])
        _write_item(items_dir, "B", "Beta",  deps=["C"])
        _write_item(items_dir, "C", "Gamma")

        analyzer = DependencyAnalyzer(items_dir=str(items_dir))
        analyzer.load_items()
        cycles = analyzer.find_circular_deps()

        assert cycles == []


class TestCriticalPath:
    @pytest.mark.unit
    def test_find_critical_path_linear_chain(self, tmp_path: Path) -> None:
        """A linear chain of 5 items should yield a critical path of length 5."""
        items_dir = tmp_path / "ITEMS"
        items_dir.mkdir()
        # E→D→C→B→A (A is root)
        _write_item(items_dir, "A", "Step 1")
        _write_item(items_dir, "B", "Step 2", deps=["A"])
        _write_item(items_dir, "C", "Step 3", deps=["B"])
        _write_item(items_dir, "D", "Step 4", deps=["C"])
        _write_item(items_dir, "E", "Step 5", deps=["D"])

        analyzer = DependencyAnalyzer(items_dir=str(items_dir))
        analyzer.load_items()
        path = analyzer.find_critical_path()

        assert len(path) == 5, f"Expected path length 5, got {len(path)}: {path}"
        # Path should be ordered (each step depends on previous)
        assert path[-1] == "E" or path[0] == "E"  # terminus at either end


class TestBottlenecks:
    @pytest.mark.unit
    def test_find_bottlenecks(self, tmp_path: Path) -> None:
        """An item blocked by 3+ others should be identified as a bottleneck."""
        items_dir = tmp_path / "ITEMS"
        items_dir.mkdir()
        # B, C, D, E all depend on A → A is a bottleneck
        _write_item(items_dir, "A", "Foundation")
        _write_item(items_dir, "B", "Feature B", deps=["A"])
        _write_item(items_dir, "C", "Feature C", deps=["A"])
        _write_item(items_dir, "D", "Feature D", deps=["A"])
        _write_item(items_dir, "E", "Feature E", deps=["A"])

        analyzer = DependencyAnalyzer(items_dir=str(items_dir))
        analyzer.load_items()
        bottlenecks = analyzer.find_bottlenecks(min_dependents=3)

        assert "A" in bottlenecks, f"A should be a bottleneck, got: {bottlenecks}"

    @pytest.mark.unit
    def test_no_bottleneck_when_few_deps(self, tmp_path: Path) -> None:
        """An item with fewer dependents than the threshold is not a bottleneck."""
        items_dir = tmp_path / "ITEMS"
        items_dir.mkdir()
        _write_item(items_dir, "A", "Root")
        _write_item(items_dir, "B", "Child B", deps=["A"])

        analyzer = DependencyAnalyzer(items_dir=str(items_dir))
        analyzer.load_items()
        bottlenecks = analyzer.find_bottlenecks(min_dependents=3)

        assert "A" not in bottlenecks


class TestD3JsonFormat:
    @pytest.mark.unit
    def test_to_d3_json_format(self, tmp_path: Path) -> None:
        """Output of to_d3_json() should have 'nodes' and 'links' keys."""
        items_dir = tmp_path / "ITEMS"
        items_dir.mkdir()
        _write_item(items_dir, "X", "Node X")
        _write_item(items_dir, "Y", "Node Y", deps=["X"])

        analyzer = DependencyAnalyzer(items_dir=str(items_dir))
        analyzer.load_items()
        result = analyzer.to_d3_json()

        assert "nodes" in result, "to_d3_json must return a 'nodes' key"
        assert "links" in result, "to_d3_json must return a 'links' key"
        assert isinstance(result["nodes"], list)
        assert isinstance(result["links"], list)

    @pytest.mark.unit
    def test_d3_node_has_required_fields(self, tmp_path: Path) -> None:
        """Each D3 node should have at minimum 'id' and 'title'."""
        items_dir = tmp_path / "ITEMS"
        items_dir.mkdir()
        _write_item(items_dir, "Z", "Node Z", status="in_progress")

        analyzer = DependencyAnalyzer(items_dir=str(items_dir))
        analyzer.load_items()
        result = analyzer.to_d3_json()

        node_z = next((n for n in result["nodes"] if n.get("id") == "Z"), None)
        assert node_z is not None
        assert "title" in node_z
        assert "status" in node_z

    @pytest.mark.unit
    def test_d3_link_has_source_target(self, tmp_path: Path) -> None:
        """D3 links should have 'source' and 'target' fields."""
        items_dir = tmp_path / "ITEMS"
        items_dir.mkdir()
        _write_item(items_dir, "P", "Parent")
        _write_item(items_dir, "Q", "Child", deps=["P"])

        analyzer = DependencyAnalyzer(items_dir=str(items_dir))
        analyzer.load_items()
        result = analyzer.to_d3_json()

        assert len(result["links"]) >= 1
        for link in result["links"]:
            assert "source" in link, "link missing 'source'"
            assert "target" in link, "link missing 'target'"


class TestUnblockedItems:
    @pytest.mark.unit
    def test_get_unblocked_items(self, tmp_path: Path) -> None:
        """Items with no incomplete deps should be in the unblocked set."""
        items_dir = tmp_path / "ITEMS"
        items_dir.mkdir()
        _write_item(items_dir, "ROOT", "Root item",  status="done")
        _write_item(items_dir, "NEXT", "Next item",  status="backlog", deps=["ROOT"])
        _write_item(items_dir, "BLCK", "Stuck item", status="backlog", deps=["MISSING_DEP"])

        analyzer = DependencyAnalyzer(items_dir=str(items_dir))
        analyzer.load_items()
        unblocked = analyzer.get_unblocked_items()

        ids = [i["id"] for i in unblocked]
        assert "NEXT" in ids, "NEXT should be unblocked (ROOT is done)"
        assert "BLCK" not in ids, "BLCK has an unresolved dep"


class TestItemDepth:
    @pytest.mark.unit
    def test_get_item_depth_root_is_zero(self, tmp_path: Path) -> None:
        """Root items (no dependencies) should have depth 0."""
        items_dir = tmp_path / "ITEMS"
        items_dir.mkdir()
        _write_item(items_dir, "ROOT", "Root")
        _write_item(items_dir, "CHILD", "Child", deps=["ROOT"])

        analyzer = DependencyAnalyzer(items_dir=str(items_dir))
        analyzer.load_items()

        assert analyzer.get_item_depth("ROOT") == 0

    @pytest.mark.unit
    def test_get_item_depth_child_is_one(self, tmp_path: Path) -> None:
        """Direct child of root should have depth 1."""
        items_dir = tmp_path / "ITEMS"
        items_dir.mkdir()
        _write_item(items_dir, "ROOT",  "Root")
        _write_item(items_dir, "CHILD", "Child", deps=["ROOT"])

        analyzer = DependencyAnalyzer(items_dir=str(items_dir))
        analyzer.load_items()

        assert analyzer.get_item_depth("CHILD") == 1

    @pytest.mark.unit
    def test_get_item_depth_grandchild_is_two(self, tmp_path: Path) -> None:
        """Grandchild (ROOT → CHILD → GRAND) should have depth 2."""
        items_dir = tmp_path / "ITEMS"
        items_dir.mkdir()
        _write_item(items_dir, "ROOT",  "Root")
        _write_item(items_dir, "CHILD", "Child", deps=["ROOT"])
        _write_item(items_dir, "GRAND", "Grandchild", deps=["CHILD"])

        analyzer = DependencyAnalyzer(items_dir=str(items_dir))
        analyzer.load_items()

        assert analyzer.get_item_depth("GRAND") == 2
