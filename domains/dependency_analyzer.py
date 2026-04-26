"""domains/dependency_analyzer.py — Roadmap item dependency graph analysis.

Parses RM-*.md files to extract dependency relationships, builds an adjacency
graph, finds the critical path via longest DAG path, detects circular dependencies
via Tarjan's SCC algorithm, and exports D3-compatible JSON.

NetworkX is used when available but not required — all algorithms have stdlib
fallbacks.
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional dependency
# ---------------------------------------------------------------------------
try:
    import networkx as nx  # type: ignore
    _NX_AVAILABLE = True
except ImportError:
    nx = None  # type: ignore[assignment]
    _NX_AVAILABLE = False
    logger.debug("networkx not available — using stdlib BFS/DFS implementations")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ITEMS_DEFAULT_DIR: str = "docs/roadmap/ITEMS"
ARTIFACTS_DIR: str = "artifacts"
GRAPH_OUTPUT_FILE: str = os.path.join(ARTIFACTS_DIR, "dependency_graph.json")
RM_ID_PATTERN: re.Pattern = re.compile(r"\bRM-[A-Z]+-\d+\b")
STATUS_DONE_VALUES: Set[str] = {"done", "completed", "accepted", "closed"}


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------
@dataclass
class DependencyNode:
    """A roadmap item modelled as a graph node.

    Attributes:
        id: RM-CATEGORY-NNN identifier.
        title: Short title parsed from the markdown heading.
        status: Current workflow status string.
        category: Category slug (e.g. 'APIGW', 'ML').
        dependents: List of item IDs that depend on this item.
        dependencies: List of item IDs this item depends on.
    """

    id: str
    title: str
    status: str = "backlog"
    category: str = ""
    dependents: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class GraphStats:
    """Summary statistics for the dependency graph.

    Attributes:
        node_count: Total number of roadmap items.
        edge_count: Total number of dependency edges.
        critical_path_length: Number of nodes on the critical path.
        critical_path: Ordered list of node IDs on the critical path.
        circular_deps: List of SCCs (each a list of node IDs) with >1 node.
        bottlenecks: Node IDs that block at least min_dependents others.
    """

    node_count: int
    edge_count: int
    critical_path_length: int
    critical_path: List[str]
    circular_deps: List[List[str]]
    bottlenecks: List[str]


# ---------------------------------------------------------------------------
# Analyser
# ---------------------------------------------------------------------------
class DependencyAnalyzer:
    """Build and analyse the roadmap item dependency graph.

    Example::

        analyzer = DependencyAnalyzer()
        analyzer.load_items()
        analyzer.build_graph()
        stats = analyzer.get_stats()
        print(stats.critical_path)
    """

    def __init__(self, items_dir: str = ITEMS_DEFAULT_DIR) -> None:
        """Initialise with the directory containing RM-*.md files.

        Args:
            items_dir: Path to the directory holding roadmap item markdown files.
        """
        self.items_dir = items_dir
        self._nodes: Dict[str, DependencyNode] = {}
        self._adj: Dict[str, List[str]] = {}     # node → nodes it depends on
        self._radj: Dict[str, List[str]] = {}    # node → nodes that depend on it
        logger.info("DependencyAnalyzer initialised (items_dir=%s)", items_dir)

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _parse_md_file(self, path: Path) -> Optional[DependencyNode]:
        """Parse a single RM-*.md file and return a DependencyNode.

        Extracts title from the first H1 heading, status from a 'status:' field,
        and dependency IDs from any line containing an RM-XXX-NNN token.

        Args:
            path: Path to the markdown file.

        Returns:
            DependencyNode or None on parse failure.
        """
        item_id = path.stem  # filename without extension
        if not re.match(r"^RM-[A-Z]+-\d+$", item_id):
            return None
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            logger.warning("_parse_md_file: cannot read %s — %s", path, exc)
            return None

        # Title: first H1 line
        title = item_id
        for line in text.splitlines():
            stripped = line.strip().lstrip("#").strip()
            if line.startswith("#") and stripped:
                title = stripped
                break

        # Status
        status = "backlog"
        status_match = re.search(r"status[:\s]+([^\n]+)", text, re.IGNORECASE)
        if status_match:
            status = status_match.group(1).strip().lower().rstrip(".,")

        # Dependencies: RM-IDs that appear after "## Dependencies" or "depends on"
        deps: List[str] = []
        dep_section = False
        for line in text.splitlines():
            line_lower = line.lower()
            if re.search(r"##\s*depend", line_lower):
                dep_section = True
                continue
            if dep_section and line.startswith("##"):
                dep_section = False
            if dep_section or "depends on" in line_lower or "blocked by" in line_lower:
                found = RM_ID_PATTERN.findall(line)
                deps.extend(f for f in found if f != item_id)

        category = item_id.split("-")[1] if "-" in item_id else ""

        return DependencyNode(
            id=item_id,
            title=title,
            status=status,
            category=category,
            dependencies=list(set(deps)),
            dependents=[],
        )

    def load_items(self) -> List[DependencyNode]:
        """Scan the items directory and load all roadmap items.

        Returns:
            List of DependencyNode objects found in the directory.
        """
        self._nodes.clear()
        items_path = Path(self.items_dir)
        if not items_path.exists():
            logger.warning("load_items: items_dir '%s' does not exist", self.items_dir)
            return []

        for md_file in sorted(items_path.glob("RM-*.md")):
            node = self._parse_md_file(md_file)
            if node:
                self._nodes[node.id] = node

        logger.info("load_items: loaded %d items from %s", len(self._nodes), self.items_dir)
        return list(self._nodes.values())

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def build_graph(self) -> None:
        """Build adjacency lists and populate the dependents field on each node.

        Writes the D3 JSON export to artifacts/dependency_graph.json.
        """
        self._adj = {node_id: list(node.dependencies) for node_id, node in self._nodes.items()}
        self._radj = {node_id: [] for node_id in self._nodes}

        for node_id, deps in self._adj.items():
            for dep_id in deps:
                if dep_id in self._radj:
                    self._radj[dep_id].append(node_id)

        # Populate dependents on node objects
        for node_id, node in self._nodes.items():
            node.dependents = list(self._radj.get(node_id, []))

        edge_count = sum(len(deps) for deps in self._adj.values())
        logger.info("build_graph: %d nodes, %d edges", len(self._nodes), edge_count)

        # Persist
        try:
            os.makedirs(ARTIFACTS_DIR, exist_ok=True)
            with open(GRAPH_OUTPUT_FILE, "w") as fh:
                json.dump(self.to_d3_json(), fh, indent=2)
            logger.info("build_graph: wrote graph to %s", GRAPH_OUTPUT_FILE)
        except Exception as exc:
            logger.warning("build_graph: could not write graph file — %s", exc)

    # ------------------------------------------------------------------
    # Critical path (longest path in DAG)
    # ------------------------------------------------------------------

    def find_critical_path(self) -> List[str]:
        """Find the longest path in the DAG by node count.

        Uses NetworkX if available, otherwise topological sort + DP.

        Returns:
            Ordered list of node IDs on the critical path.
        """
        if not self._nodes:
            return []

        if _NX_AVAILABLE:
            return self._nx_critical_path()
        return self._stdlib_critical_path()

    def _nx_critical_path(self) -> List[str]:
        """Critical path via NetworkX DAG longest path.

        Returns:
            List of node IDs.
        """
        G = nx.DiGraph()
        for node_id in self._nodes:
            G.add_node(node_id)
        for node_id, deps in self._adj.items():
            for dep_id in deps:
                G.add_edge(dep_id, node_id)  # dep → dependant direction
        try:
            path = nx.dag_longest_path(G)
            return list(path)
        except Exception as exc:
            logger.warning("_nx_critical_path: %s", exc)
            return []

    def _stdlib_critical_path(self) -> List[str]:
        """Critical path via topological sort and dynamic programming.

        Returns:
            List of node IDs.
        """
        # Build topo order
        try:
            order = self._topological_sort()
        except ValueError:
            logger.warning("_stdlib_critical_path: cycle detected, cannot compute critical path")
            return []

        # DP: dist[v] = (longest path length ending at v, predecessor)
        dist: Dict[str, int] = {n: 1 for n in self._nodes}
        pred: Dict[str, Optional[str]] = {n: None for n in self._nodes}

        for node_id in order:
            for dep_id in self._adj.get(node_id, []):
                if dep_id in dist and dist[dep_id] + 1 > dist[node_id]:
                    dist[node_id] = dist[dep_id] + 1
                    pred[node_id] = dep_id

        # Find end of longest path
        end = max(dist, key=dist.__getitem__)
        path: List[str] = []
        cur: Optional[str] = end
        while cur is not None:
            path.append(cur)
            cur = pred.get(cur)
        path.reverse()
        return path

    def _topological_sort(self) -> List[str]:
        """Kahn's algorithm topological sort.

        Returns:
            Topologically sorted list of node IDs.

        Raises:
            ValueError: If a cycle is detected.
        """
        in_degree: Dict[str, int] = {n: 0 for n in self._nodes}
        for deps in self._adj.values():
            for dep in deps:
                if dep in in_degree:
                    in_degree[dep] = in_degree[dep]  # no-op; dependency is a prereq
        # Recompute: in_degree = number of prerequisites each node has
        in_degree = {n: len([d for d in self._adj.get(n, []) if d in self._nodes])
                     for n in self._nodes}

        queue = [n for n, d in in_degree.items() if d == 0]
        result: List[str] = []
        while queue:
            node = queue.pop(0)
            result.append(node)
            for dependent in self._radj.get(node, []):
                if dependent in in_degree:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)

        if len(result) != len(self._nodes):
            raise ValueError("Graph contains cycles — topological sort failed")
        return result

    # ------------------------------------------------------------------
    # Cycle detection (Tarjan's SCC)
    # ------------------------------------------------------------------

    def find_circular_deps(self) -> List[List[str]]:
        """Find strongly connected components with more than one node.

        Uses Tarjan's SCC algorithm regardless of NetworkX availability.

        Returns:
            List of SCCs (each a list of node IDs) representing circular deps.
        """
        index_counter = [0]
        stack: List[str] = []
        on_stack: Set[str] = set()
        index: Dict[str, int] = {}
        lowlink: Dict[str, int] = {}
        sccs: List[List[str]] = []

        def strongconnect(v: str) -> None:
            index[v] = index_counter[0]
            lowlink[v] = index_counter[0]
            index_counter[0] += 1
            stack.append(v)
            on_stack.add(v)

            for w in self._adj.get(v, []):
                if w not in self._nodes:
                    continue
                if w not in index:
                    strongconnect(w)
                    lowlink[v] = min(lowlink[v], lowlink[w])
                elif w in on_stack:
                    lowlink[v] = min(lowlink[v], index[w])

            if lowlink[v] == index[v]:
                scc: List[str] = []
                while True:
                    w = stack.pop()
                    on_stack.discard(w)
                    scc.append(w)
                    if w == v:
                        break
                sccs.append(scc)

        for node_id in self._nodes:
            if node_id not in index:
                strongconnect(node_id)

        cycles = [scc for scc in sccs if len(scc) > 1]
        logger.info("find_circular_deps: found %d circular dependency groups", len(cycles))
        return cycles

    # ------------------------------------------------------------------
    # Bottleneck analysis
    # ------------------------------------------------------------------

    def find_bottlenecks(self, min_dependents: int = 3) -> List[str]:
        """Find items that directly block at least min_dependents other items.

        Args:
            min_dependents: Minimum number of direct dependents to qualify.

        Returns:
            List of node IDs that are bottlenecks, sorted by dependent count desc.
        """
        bottlenecks = [
            node_id
            for node_id, dependents in self._radj.items()
            if len(dependents) >= min_dependents
        ]
        bottlenecks.sort(key=lambda n: len(self._radj.get(n, [])), reverse=True)
        logger.info("find_bottlenecks(min=%d): found %d bottlenecks", min_dependents, len(bottlenecks))
        return bottlenecks

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> GraphStats:
        """Return a summary of the dependency graph.

        Returns:
            GraphStats dataclass populated with current graph analysis.
        """
        critical = self.find_critical_path()
        circular = self.find_circular_deps()
        bottlenecks = self.find_bottlenecks()
        edge_count = sum(len(deps) for deps in self._adj.values())

        return GraphStats(
            node_count=len(self._nodes),
            edge_count=edge_count,
            critical_path_length=len(critical),
            critical_path=critical,
            circular_deps=circular,
            bottlenecks=bottlenecks,
        )

    # ------------------------------------------------------------------
    # D3 export
    # ------------------------------------------------------------------

    def to_d3_json(self) -> dict:
        """Export the graph as D3.js-compatible JSON.

        Each node has an id, title, status, category, and group (numeric category index).
        Each link has source, target, and value=1.

        Returns:
            Dict with 'nodes' and 'links' keys.
        """
        categories = sorted(set(n.category for n in self._nodes.values()))
        cat_index = {c: i for i, c in enumerate(categories)}

        nodes = [
            {
                "id": node.id,
                "title": node.title,
                "status": node.status,
                "category": node.category,
                "group": cat_index.get(node.category, 0),
            }
            for node in self._nodes.values()
        ]
        links = [
            {"source": dep_id, "target": node_id, "value": 1}
            for node_id, deps in self._adj.items()
            for dep_id in deps
            if dep_id in self._nodes
        ]
        return {"nodes": nodes, "links": links}

    # ------------------------------------------------------------------
    # Depth & unblocked
    # ------------------------------------------------------------------

    def get_item_depth(self, item_id: str) -> int:
        """Return the depth (distance from root) of an item in the DAG.

        Root nodes (no dependencies) have depth 0.

        Args:
            item_id: Node ID to query.

        Returns:
            Integer depth, or -1 if the item is not found.
        """
        if item_id not in self._nodes:
            return -1

        # BFS from roots to find shortest path to item_id
        visited: Dict[str, int] = {}
        queue: List[Tuple[str, int]] = [(item_id, 0)]
        # Instead: BFS from item_id upward through dependencies
        depth = 0
        current_level = {item_id}
        while True:
            parents: Set[str] = set()
            for node_id in current_level:
                for dep in self._adj.get(node_id, []):
                    if dep in self._nodes:
                        parents.add(dep)
            if not parents:
                break
            depth += 1
            current_level = parents
            if depth > len(self._nodes):
                break  # cycle guard

        return depth

    def get_unblocked_items(self) -> List[str]:
        """Return item IDs whose dependencies are all completed.

        An item is 'unblocked' when every item in its dependency list has a
        status that belongs to STATUS_DONE_VALUES.

        Returns:
            List of item IDs that are ready to be worked on.
        """
        unblocked: List[str] = []
        for node_id, node in self._nodes.items():
            if node.status.lower() in STATUS_DONE_VALUES:
                continue
            deps = self._adj.get(node_id, [])
            if not deps:
                unblocked.append(node_id)
                continue
            all_done = all(
                self._nodes.get(d, DependencyNode("", "")).status.lower() in STATUS_DONE_VALUES
                for d in deps
                if d in self._nodes
            )
            if all_done:
                unblocked.append(node_id)

        logger.info("get_unblocked_items: %d items ready", len(unblocked))
        return unblocked

    def analyze_from_plane(self) -> dict:
        """Build a dependency graph from live Plane CE issues instead of markdown.

        Reads all issues from the Plane API, builds the same adjacency structure
        as load_items()/build_graph(), and returns D3-compatible JSON plus derived
        metrics.  Falls back to an empty graph if Plane is not reachable.
        """
        try:
            from framework.plane_connector import PlaneAPI
            api = PlaneAPI()
            if not api.health_check():
                return {"error": "Plane not reachable", "nodes": [], "links": []}

            issues = api.list_all_issues()
            self._nodes.clear()

            for iss in issues:
                name = iss.get("name", "")
                # RM-* issues have [RM-XXX-NNN] prefix in their Plane title
                m = re.match(r"^\[([A-Z]+-[A-Z]+-\d+)\]", name)
                rm_id = m.group(1) if m else iss.get("id", "")
                state_name = iss.get("state__name") or iss.get("state", "Backlog")
                if isinstance(state_name, dict):
                    state_name = state_name.get("name", "Backlog")

                # Parse depends_on from description HTML (looks for RM-* patterns)
                desc = iss.get("description_html") or iss.get("description") or ""
                deps = list({m.group() for m in RM_ID_PATTERN.finditer(desc) if m.group() != rm_id})

                self._nodes[rm_id] = DependencyNode(
                    id=rm_id,
                    status=state_name,
                    dependencies=deps,
                    title=name[:80],
                )

            self._adj = {nid: list(node.dependencies) for nid, node in self._nodes.items()}
            self._radj = {nid: [] for nid in self._nodes}
            for nid, deps in self._adj.items():
                for dep in deps:
                    if dep in self._radj:
                        self._radj[dep].append(nid)

            return {
                "graph":         self.to_d3_json(),
                "unblocked":     self.get_unblocked_items(),
                "critical_path": self.find_critical_path(),
                "bottlenecks":   self.find_bottlenecks(),
                "stats":         {"total": len(self._nodes), "source": "plane"},
            }
        except Exception as exc:
            logger.warning("analyze_from_plane failed: %s", exc)
            return {"error": str(exc), "nodes": [], "links": []}
