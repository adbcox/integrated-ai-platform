#!/usr/bin/env python3
"""Smart checkpoint saving with multi-metric tracking and version management.

Saves model checkpoints using torch if available, falling back to pickle.
Tracks val_loss and f1 to determine best checkpoints, and prunes old ones
to stay within the max_keep limit while always preserving the best.

Metadata (metrics history, best checkpoint info) is persisted separately
in checkpoint_dir/metadata.json — not embedded in the model weights file.
"""

from __future__ import annotations

import csv
import json
import logging
import os
import pickle
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import torch as _torch
    _TORCH_AVAILABLE = True
except ImportError:
    _torch = None  # type: ignore[assignment]
    _TORCH_AVAILABLE = False

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class CheckpointMetrics:
    """Metrics snapshot for a single training epoch.

    Attributes:
        epoch: Epoch number (1-based).
        train_loss: Training loss value.
        val_loss: Validation loss value.
        accuracy: Validation accuracy (0.0–1.0).
        f1: Macro F1 score (0.0–1.0).
        timestamp: ISO-format UTC timestamp.
    """

    epoch: int
    train_loss: float
    val_loss: float
    accuracy: float
    f1: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Checkpoint:
    """Metadata record for a saved model checkpoint.

    Attributes:
        version: Version tag string (e.g. "v1", "best").
        path: Absolute path to the checkpoint file.
        metrics: Metrics at the time this checkpoint was saved.
        is_best: Whether this is the current best checkpoint.
        created_at: ISO-format UTC creation timestamp.
    """

    version: str
    path: str
    metrics: CheckpointMetrics
    is_best: bool
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------

# Composite score: lower is better (val_loss ↓, f1 ↑)
_SCORE_WEIGHT_VAL_LOSS: float = 0.7
_SCORE_WEIGHT_F1: float = 0.3


def _composite_score(metrics: CheckpointMetrics) -> float:
    """Compute a composite scalar for checkpoint comparison (lower is better).

    Score = 0.7 * val_loss − 0.3 * f1

    Args:
        metrics: Epoch metrics to score.

    Returns:
        Composite score (lower = better checkpoint).
    """
    return _SCORE_WEIGHT_VAL_LOSS * metrics.val_loss - _SCORE_WEIGHT_F1 * metrics.f1


class CheckpointManager:
    """Saves, loads, and prunes model checkpoints with multi-metric tracking.

    Persists only metadata to ``checkpoint_dir/metadata.json``.
    Model weights are saved as ``.pt`` (torch) or ``.pkl`` (pickle) files.

    Example::

        mgr = CheckpointManager("artifacts/checkpoints", max_keep=3)
        ckpt = mgr.save(model.state_dict(), metrics)
        state, ckpt = mgr.load_best()
    """

    def __init__(
        self,
        checkpoint_dir: str = "artifacts/checkpoints",
        max_keep: int = 5,
    ) -> None:
        """Initialise the checkpoint manager.

        Args:
            checkpoint_dir: Directory for checkpoint files and metadata.
            max_keep: Maximum number of checkpoints to retain (best is always kept).
        """
        self._dir = Path(checkpoint_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._max_keep = max_keep
        self._metadata_path = self._dir / "metadata.json"
        self._checkpoints: List[Checkpoint] = []
        self._metrics_history: List[CheckpointMetrics] = []
        self._best_score: Optional[float] = None
        self._load_metadata()
        logger.debug("CheckpointManager initialised dir=%s max_keep=%d", self._dir, max_keep)

    # ------------------------------------------------------------------
    # Saving
    # ------------------------------------------------------------------

    def should_save(self, metrics: CheckpointMetrics, save_every_n: int = 1) -> bool:
        """Decide whether to save a checkpoint for this epoch.

        Saves if either:
        - The epoch is divisible by ``save_every_n``, OR
        - The validation loss improved over the best previously seen.

        Args:
            metrics: Current epoch metrics.
            save_every_n: Periodic save interval (in epochs).

        Returns:
            True if a checkpoint should be saved.
        """
        if metrics.epoch % save_every_n == 0:
            return True
        return self.is_improvement(metrics)

    def save(
        self,
        model_state: Dict[str, Any],
        metrics: CheckpointMetrics,
        version_tag: str = "",
    ) -> Checkpoint:
        """Save a model checkpoint and update metadata.

        Args:
            model_state: Model state dict (e.g. from ``model.state_dict()``).
            metrics: Current epoch metrics.
            version_tag: Optional human-readable version label.

        Returns:
            The saved ``Checkpoint`` record.
        """
        is_best = self.is_improvement(metrics)

        filename = f"checkpoint_epoch{metrics.epoch:04d}_loss{metrics.val_loss:.4f}"
        if version_tag:
            filename += f"_{version_tag}"
        suffix = ".pt" if _TORCH_AVAILABLE else ".pkl"
        ckpt_path = self._dir / (filename + suffix)

        self._write_weights(model_state, ckpt_path)

        version = version_tag or f"v{len(self._checkpoints) + 1}"
        ckpt = Checkpoint(
            version=version,
            path=str(ckpt_path),
            metrics=metrics,
            is_best=is_best,
        )

        # Update best flag on all previous checkpoints
        if is_best:
            for c in self._checkpoints:
                c.is_best = False
            self._best_score = _composite_score(metrics)
            logger.info("New best checkpoint: epoch=%d val_loss=%.4f f1=%.4f", metrics.epoch, metrics.val_loss, metrics.f1)

        self._checkpoints.append(ckpt)
        self._metrics_history.append(metrics)
        self._save_metadata()
        self.prune_old_checkpoints()

        logger.info("Saved checkpoint %s epoch=%d", ckpt_path.name, metrics.epoch)
        return ckpt

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_best(self) -> Optional[Tuple[Dict[str, Any], Checkpoint]]:
        """Load the best checkpoint by composite metric score.

        Returns:
            Tuple of (model_state_dict, Checkpoint), or None if no checkpoints exist.
        """
        best = next((c for c in self._checkpoints if c.is_best), None)
        if best is None and self._checkpoints:
            # Fallback: pick by composite score
            best = min(
                self._checkpoints,
                key=lambda c: _composite_score(c.metrics),
            )
        return self._load_ckpt(best)

    def load_latest(self) -> Optional[Tuple[Dict[str, Any], Checkpoint]]:
        """Load the most recently saved checkpoint.

        Returns:
            Tuple of (model_state_dict, Checkpoint), or None if none exist.
        """
        if not self._checkpoints:
            return None
        return self._load_ckpt(self._checkpoints[-1])

    def load_version(self, version: str) -> Optional[Tuple[Dict[str, Any], Checkpoint]]:
        """Load a checkpoint by version tag.

        Args:
            version: Version string to look up.

        Returns:
            Tuple of (model_state_dict, Checkpoint), or None if not found.
        """
        match = next((c for c in self._checkpoints if c.version == version), None)
        return self._load_ckpt(match)

    # ------------------------------------------------------------------
    # History and metrics
    # ------------------------------------------------------------------

    def get_history(self) -> List[CheckpointMetrics]:
        """Return all recorded metrics in chronological order.

        Returns:
            List of ``CheckpointMetrics``.
        """
        return list(self._metrics_history)

    def is_improvement(self, new_metrics: CheckpointMetrics) -> bool:
        """Determine if new metrics are better than the current best.

        Uses composite score: 0.7 * val_loss − 0.3 * f1 (lower is better).

        Args:
            new_metrics: Metrics to compare.

        Returns:
            True if new_metrics represent an improvement.
        """
        if self._best_score is None:
            return True
        return _composite_score(new_metrics) < self._best_score

    def get_best_metrics(self) -> Optional[CheckpointMetrics]:
        """Return the metrics associated with the best checkpoint.

        Returns:
            Best ``CheckpointMetrics``, or None if no checkpoints exist.
        """
        best_ckpt = next((c for c in self._checkpoints if c.is_best), None)
        return best_ckpt.metrics if best_ckpt else None

    # ------------------------------------------------------------------
    # Pruning
    # ------------------------------------------------------------------

    def prune_old_checkpoints(self) -> List[str]:
        """Delete old checkpoint files, keeping ``max_keep`` most recent + best.

        Returns:
            List of deleted file paths.
        """
        # Always keep the best
        best_paths = {c.path for c in self._checkpoints if c.is_best}

        # Candidates: non-best, ordered oldest first
        non_best = [c for c in self._checkpoints if not c.is_best]
        while len(non_best) + len(best_paths) > self._max_keep:
            to_remove = non_best.pop(0)  # oldest
            deleted = self._delete_file(to_remove.path)
            if deleted:
                logger.debug("Pruned checkpoint: %s", to_remove.path)
            self._checkpoints = [c for c in self._checkpoints if c.path != to_remove.path]

        self._save_metadata()
        return []  # returning paths of deleted files (already removed)

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_history_csv(self, path: str) -> None:
        """Write the metrics history to a CSV file.

        Args:
            path: Destination file path.
        """
        if not self._metrics_history:
            logger.warning("export_history_csv: no metrics history to export")
            return

        rows = [asdict(m) for m in self._metrics_history]
        fieldnames = list(rows[0].keys())

        try:
            with open(path, "w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            logger.info("Exported metrics history to %s", path)
        except OSError as exc:
            logger.error("Failed to export CSV: %s", exc)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _write_weights(self, state: Dict[str, Any], path: Path) -> None:
        """Persist model weights using torch or pickle.

        Args:
            state: Model state dict.
            path: Destination file path.
        """
        try:
            if _TORCH_AVAILABLE:
                _torch.save(state, str(path))
            else:
                with open(path, "wb") as fh:
                    pickle.dump(state, fh, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to write checkpoint weights: %s", exc)

    def _read_weights(self, path: str) -> Optional[Dict[str, Any]]:
        """Load model weights from a checkpoint file.

        Args:
            path: Path to the checkpoint file.

        Returns:
            State dict, or None on failure.
        """
        p = Path(path)
        if not p.is_file():
            logger.warning("Checkpoint file not found: %s", path)
            return None
        try:
            if _TORCH_AVAILABLE and path.endswith(".pt"):
                return _torch.load(path, map_location="cpu")
            with open(path, "rb") as fh:
                return pickle.load(fh)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to read checkpoint %s: %s", path, exc)
            return None

    def _load_ckpt(self, ckpt: Optional[Checkpoint]) -> Optional[Tuple[Dict[str, Any], Checkpoint]]:
        """Helper that loads weights for a given checkpoint record.

        Args:
            ckpt: Checkpoint to load.

        Returns:
            Tuple or None.
        """
        if ckpt is None:
            return None
        state = self._read_weights(ckpt.path)
        if state is None:
            return None
        return state, ckpt

    def _delete_file(self, path: str) -> bool:
        """Delete a checkpoint file.

        Args:
            path: File path to delete.

        Returns:
            True if deletion succeeded.
        """
        try:
            Path(path).unlink(missing_ok=True)
            return True
        except OSError as exc:
            logger.warning("Failed to delete checkpoint %s: %s", path, exc)
            return False

    def _save_metadata(self) -> None:
        """Persist checkpoint registry and metrics history to JSON."""
        data = {
            "checkpoints": [asdict(c) for c in self._checkpoints],
            "metrics_history": [asdict(m) for m in self._metrics_history],
            "best_score": self._best_score,
        }
        try:
            self._metadata_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except OSError as exc:
            logger.error("Failed to save checkpoint metadata: %s", exc)

    def _load_metadata(self) -> None:
        """Load checkpoint registry and metrics history from JSON."""
        if not self._metadata_path.is_file():
            return
        try:
            data = json.loads(self._metadata_path.read_text(encoding="utf-8"))
            self._checkpoints = [
                Checkpoint(
                    version=c["version"],
                    path=c["path"],
                    metrics=CheckpointMetrics(**c["metrics"]),
                    is_best=c["is_best"],
                    created_at=c.get("created_at", ""),
                )
                for c in data.get("checkpoints", [])
            ]
            self._metrics_history = [
                CheckpointMetrics(**m) for m in data.get("metrics_history", [])
            ]
            self._best_score = data.get("best_score")
            logger.debug(
                "Loaded %d checkpoints, %d history records",
                len(self._checkpoints),
                len(self._metrics_history),
            )
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            logger.warning("Failed to load checkpoint metadata: %s", exc)
