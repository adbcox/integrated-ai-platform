"""domains/priority_engine.py — Multi-criteria roadmap item prioritisation.

Scores roadmap items on strategic value, urgency, effort, and risk; ranks the
full backlog; identifies quick wins; and optionally syncs priorities to Plane CE.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional dependencies
# ---------------------------------------------------------------------------
try:
    import requests  # type: ignore
    _REQUESTS_AVAILABLE = True
except ImportError:
    requests = None  # type: ignore[assignment]
    _REQUESTS_AVAILABLE = False

try:
    from framework.event_bus import publish_event  # type: ignore
except ImportError:
    def publish_event(name: str, payload: dict) -> None:  # type: ignore[misc]
        logger.debug("event_bus unavailable — skipped event: %s", name)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ITEMS_DEFAULT_DIR: str = "docs/roadmap/ITEMS"
ARTIFACTS_DIR: str = "artifacts"
RANKING_OUTPUT_FILE: str = os.path.join(ARTIFACTS_DIR, "priority_ranking.json")

URGENCY_MAP: Dict[str, float] = {
    "critical": 5.0,
    "high": 4.0,
    "medium": 3.0,
    "low": 2.0,
}
EFFORT_MAP: Dict[str, float] = {
    "s": 1.0,
    "m": 2.0,
    "l": 3.0,
    "xl": 4.0,
}
PLANE_API_RATE_LIMIT_SECONDS: float = 1.5
PLANE_TOP_N_SYNC: int = 50
REQUEST_TIMEOUT: int = 15
QUICK_WIN_VALUE_THRESHOLD: float = 7.0
QUICK_WIN_LOE_ALLOWED: set = {"s", "m"}
BOTTLENECK_BOOST_PER_DEPENDENT: float = 1.0


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------
@dataclass
class PriorityWeights:
    """Weights for the multi-criteria priority scoring formula.

    Attributes:
        value: Weight for strategic value (default 0.4).
        urgency: Weight for urgency/priority field (default 0.3).
        effort: Weight subtracted for effort (default 0.2).
        risk: Weight subtracted for execution risk (default 0.1).
    """

    value: float = 0.4
    urgency: float = 0.3
    effort: float = 0.2
    risk: float = 0.1


@dataclass
class PriorityScore:
    """Computed priority score for a single roadmap item.

    Attributes:
        item_id: RM-CATEGORY-NNN identifier.
        raw_score: Weighted multi-criteria score before rank assignment.
        rank: Position in the sorted ranking (1 = highest priority).
        quick_win: True if high value and low/medium effort.
        blocked_count: Number of other items this item currently blocks.
        last_updated: ISO-8601 timestamp of when the score was computed.
    """

    item_id: str
    raw_score: float
    rank: int = 0
    quick_win: bool = False
    blocked_count: int = 0
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
class PriorityEngine:
    """Score, rank, and export roadmap item priorities.

    Example::

        engine = PriorityEngine()
        items = engine.load_items()
        ranked = engine.rank_all()
        print(engine.export_ranked_list())
    """

    def __init__(
        self,
        weights: Optional[PriorityWeights] = None,
        items_dir: str = ITEMS_DEFAULT_DIR,
    ) -> None:
        """Initialise the engine with scoring weights and items directory.

        Args:
            weights: PriorityWeights instance (defaults to standard weights).
            items_dir: Path to RM-*.md item files.
        """
        self.weights = weights or PriorityWeights()
        self.items_dir = items_dir
        self._raw_items: List[dict] = []
        self._scores: List[PriorityScore] = []
        logger.info("PriorityEngine initialised (items_dir=%s)", items_dir)

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _parse_item_file(self, path: Path) -> Optional[dict]:
        """Parse a single RM-*.md file and extract priority-relevant fields.

        Extracts: strategic_value, priority, loe, execution_risk,
        dependency_burden, and title.

        Args:
            path: Path to the markdown file.

        Returns:
            Dict with extracted fields, or None on failure.
        """
        item_id = path.stem
        if not re.match(r"^RM-[A-Z]+-\d+$", item_id):
            return None
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            logger.warning("_parse_item_file: cannot read %s — %s", path, exc)
            return None

        # Title
        title = item_id
        for line in text.splitlines():
            if line.startswith("#"):
                title = line.lstrip("#").strip()
                break

        def _extract_field(pattern: str, default: str) -> str:
            m = re.search(pattern, text, re.IGNORECASE)
            return m.group(1).strip() if m else default

        raw_value = _extract_field(r"strategic.?value[:\s]+(\d+(?:\.\d+)?)", "5")
        raw_priority = _extract_field(r"priority[:\s]+(\w+)", "medium")
        raw_loe = _extract_field(r"\bloe[:\s]+(\w+)", "m")
        raw_risk = _extract_field(r"execution.?risk[:\s]+(\d+(?:\.\d+)?|\w+)", "3")
        raw_dep_burden = _extract_field(r"dependency.?burden[:\s]+(\d+(?:\.\d+)?)", "0")
        status = _extract_field(r"status[:\s]+([^\n]+)", "backlog").lower().rstrip(".,")

        # Parse risk — may be numeric or keyword
        try:
            risk_val = float(raw_risk)
        except ValueError:
            risk_map = {"low": 1.0, "medium": 3.0, "high": 6.0, "critical": 9.0}
            risk_val = risk_map.get(raw_risk.lower(), 3.0)

        return {
            "id": item_id,
            "title": title,
            "status": status,
            "strategic_value": float(raw_value),
            "priority": raw_priority.lower(),
            "loe": raw_loe.lower(),
            "execution_risk": risk_val,
            "dependency_burden": float(raw_dep_burden),
        }

    def load_items(self) -> List[dict]:
        """Load all RM-*.md items from the items directory.

        Returns:
            List of item dicts with parsed priority fields.
        """
        self._raw_items = []
        items_path = Path(self.items_dir)
        if not items_path.exists():
            logger.warning("load_items: items_dir '%s' does not exist", self.items_dir)
            return []

        for md_file in sorted(items_path.glob("RM-*.md")):
            item = self._parse_item_file(md_file)
            if item:
                self._raw_items.append(item)

        logger.info("load_items: loaded %d items", len(self._raw_items))
        return self._raw_items

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def score_item(
        self,
        item: dict,
        dependency_analyzer=None,
    ) -> PriorityScore:
        """Compute the priority score for a single item.

        Formula:
            raw_score = (strategic_value * w.value
                         + urgency_score * w.urgency
                         - effort_score * w.effort
                         - normalised_risk * w.risk)
                        + bottleneck_boost

        Args:
            item: Dict with fields: strategic_value, priority, loe,
                  execution_risk, id.
            dependency_analyzer: Optional DependencyAnalyzer for blocked_count.

        Returns:
            PriorityScore with computed score and metadata.
        """
        w = self.weights
        strategic_value = float(item.get("strategic_value", 5.0))
        urgency_score = URGENCY_MAP.get(item.get("priority", "medium").lower(), 3.0)
        effort_score = EFFORT_MAP.get(item.get("loe", "m").lower(), 2.0)
        execution_risk = float(item.get("execution_risk", 3.0))
        risk_norm = execution_risk / 10.0  # normalise to 0–1

        raw_score = (
            strategic_value * w.value
            + urgency_score * w.urgency
            - effort_score * w.effort
            - risk_norm * w.risk
        )

        # Bottleneck boost
        blocked_count = 0
        if dependency_analyzer is not None:
            item_id = item.get("id", "")
            blocked_count = len(dependency_analyzer._radj.get(item_id, []))
            raw_score += blocked_count * BOTTLENECK_BOOST_PER_DEPENDENT

        loe = item.get("loe", "m").lower()
        quick_win = strategic_value >= QUICK_WIN_VALUE_THRESHOLD and loe in QUICK_WIN_LOE_ALLOWED

        return PriorityScore(
            item_id=item.get("id", ""),
            raw_score=round(raw_score, 4),
            quick_win=quick_win,
            blocked_count=blocked_count,
        )

    def rank_all(self, dependency_analyzer=None) -> List[PriorityScore]:
        """Score and rank all loaded items.

        Args:
            dependency_analyzer: Optional DependencyAnalyzer for bottleneck boosts.

        Returns:
            List of PriorityScore objects sorted by raw_score descending.
        """
        if not self._raw_items:
            self.load_items()

        scores = [self.score_item(item, dependency_analyzer) for item in self._raw_items]
        scores.sort(key=lambda s: s.raw_score, reverse=True)
        for rank, score in enumerate(scores, start=1):
            score.rank = rank

        self._scores = scores
        return scores

    def get_quick_wins(self, limit: int = 10) -> List[PriorityScore]:
        """Return the top quick-win items.

        Args:
            limit: Maximum number of quick wins to return.

        Returns:
            List of PriorityScore objects flagged as quick wins.
        """
        if not self._scores:
            self.rank_all()
        return [s for s in self._scores if s.quick_win][:limit]

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_ranked_list(self) -> str:
        """Format the ranked list as a Markdown table.

        Returns:
            Markdown string with columns: rank, id, title, score, quick_win.
        """
        if not self._scores:
            self.rank_all()

        item_map = {item["id"]: item for item in self._raw_items}
        lines = [
            "| Rank | ID | Title | Score | Quick Win |",
            "|------|-----|-------|-------|-----------|",
        ]
        for score in self._scores:
            item = item_map.get(score.item_id, {})
            title = item.get("title", score.item_id)[:60]
            qw = "Yes" if score.quick_win else ""
            lines.append(
                f"| {score.rank} | {score.item_id} | {title} | {score.raw_score:.2f} | {qw} |"
            )
        return "\n".join(lines)

    def rerank_and_save(
        self,
        output_path: str = RANKING_OUTPUT_FILE,
        dependency_analyzer=None,
    ) -> None:
        """Run a full rank pass and save results to JSON.

        Args:
            output_path: Path to write the ranking JSON file.
            dependency_analyzer: Optional DependencyAnalyzer for boost data.
        """
        scores = self.rank_all(dependency_analyzer)
        try:
            os.makedirs(ARTIFACTS_DIR, exist_ok=True)
            data = {
                "generated_at": datetime.utcnow().isoformat(),
                "rankings": [asdict(s) for s in scores],
            }
            with open(output_path, "w") as fh:
                json.dump(data, fh, indent=2)
            logger.info("rerank_and_save: wrote %d rankings to %s", len(scores), output_path)
        except Exception as exc:
            logger.warning("rerank_and_save: %s", exc)

        publish_event("roadmap.priority.updated", {"ranked_count": len(scores)})

    # ------------------------------------------------------------------
    # Plane CE sync
    # ------------------------------------------------------------------

    def update_plane_priorities(
        self,
        api_token: str,
        workspace: str,
        project_id: str,
        dry_run: bool = True,
    ) -> None:
        """Sync the top-ranked items' priorities to Plane CE.

        Rate limited to PLANE_API_RATE_LIMIT_SECONDS between API calls.

        Args:
            api_token: Plane API token.
            workspace: Plane workspace slug.
            project_id: Plane project UUID.
            dry_run: If True, log actions without making API calls.
        """
        if not self._scores:
            self.rank_all()

        top = self._scores[:PLANE_TOP_N_SYNC]
        item_map = {item["id"]: item for item in self._raw_items}

        plane_priority_map = {1: "urgent", 2: "high", 3: "medium", 4: "low"}

        for score in top:
            plane_priority = plane_priority_map.get(
                min(score.rank // 10 + 1, 4), "none"
            )
            item = item_map.get(score.item_id, {})
            issue_title = item.get("title", score.item_id)

            if dry_run:
                logger.info(
                    "[DRY RUN] Would set priority='%s' for '%s' (rank=%d score=%.2f)",
                    plane_priority, score.item_id, score.rank, score.raw_score,
                )
                continue

            if not _REQUESTS_AVAILABLE:
                logger.warning("update_plane_priorities: requests unavailable")
                break

            try:
                url = (
                    f"https://api.plane.so/api/v1/workspaces/{workspace}"
                    f"/projects/{project_id}/issues/"
                )
                headers = {"x-api-token": api_token, "Content-Type": "application/json"}
                resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
                resp.raise_for_status()
                issues = resp.json().get("results", [])
                matched = [i for i in issues if score.item_id in (i.get("name", "") + i.get("description_html", ""))]
                for issue in matched:
                    patch_url = f"{url}{issue['id']}/"
                    requests.patch(
                        patch_url,
                        headers=headers,
                        json={"priority": plane_priority},
                        timeout=REQUEST_TIMEOUT,
                    )
                    logger.info("update_plane_priorities: set %s → %s", score.item_id, plane_priority)
            except Exception as exc:
                logger.warning("update_plane_priorities: %s — %s", score.item_id, exc)

            time.sleep(PLANE_API_RATE_LIMIT_SECONDS)
