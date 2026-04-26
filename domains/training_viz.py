#!/usr/bin/env python3
"""Real-time training visualization data generation for the AI dashboard.

Appends training metrics to a JSONL log, computes loss curves, gradient
statistics, weight distributions, confusion matrices, and serializes
everything into dashboard-ready payloads. No ML dependencies required
at runtime — all computation uses standard Python.
"""

from __future__ import annotations

import json
import logging
import math
import statistics
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_EXPLODING_THRESHOLD: float = 100.0   # max_abs > this → exploding gradient
_VANISHING_THRESHOLD: float = 1e-7    # mean < this → vanishing gradient
_OVERFITTING_WINDOW: int = 3          # consecutive epochs to detect overfitting

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class LossCurve:
    """Training and validation loss across epochs.

    Attributes:
        epochs: Epoch indices (1-based).
        train_loss: Training loss per epoch.
        val_loss: Validation loss per epoch.
        overfitting_detected: True if val_loss increased for 3+ consecutive
            epochs while train_loss decreased in the same window.
    """

    epochs: List[int]
    train_loss: List[float]
    val_loss: List[float]
    overfitting_detected: bool


@dataclass
class GradientStats:
    """Statistical summary of gradients for a single model layer.

    Attributes:
        layer_name: Name of the layer.
        mean: Mean of absolute gradient values.
        std: Standard deviation of gradient values.
        max_abs: Maximum absolute gradient value.
        is_exploding: True if max_abs > 100.
        is_vanishing: True if mean < 1e-7.
    """

    layer_name: str
    mean: float
    std: float
    max_abs: float
    is_exploding: bool
    is_vanishing: bool


@dataclass
class TrainingSnapshot:
    """Complete training state at a single epoch.

    Attributes:
        epoch: Epoch number.
        loss_curve: Loss curve up to and including this epoch.
        gradient_stats: Per-layer gradient statistics at this epoch.
        timestamp: ISO-format UTC timestamp.
    """

    epoch: int
    loss_curve: LossCurve
    gradient_stats: List[GradientStats]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# Visualizer
# ---------------------------------------------------------------------------


class TrainingVisualizer:
    """Records training metrics and exposes dashboard-ready visualization data.

    Reads and writes from a JSONL log file. No torch or numpy dependency
    needed at runtime — all computations use the stdlib ``statistics`` module.

    Example::

        viz = TrainingVisualizer("artifacts/training_log.jsonl")
        viz.record_epoch(1, train_loss=1.5, val_loss=1.8, learning_rate=5e-4)
        payload = viz.get_dashboard_payload()
    """

    def __init__(self, log_path: str = "artifacts/training_log.jsonl") -> None:
        """Initialise the visualizer.

        Args:
            log_path: Path to the JSONL training log file.
        """
        self._log_path = Path(log_path)
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        self._gradient_log: Dict[int, List[GradientStats]] = {}  # epoch → stats
        logger.debug("TrainingVisualizer initialised log=%s", self._log_path)

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def record_epoch(
        self,
        epoch: int,
        train_loss: float,
        val_loss: float,
        learning_rate: float,
        extra_metrics: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Append an epoch record to the JSONL log.

        Args:
            epoch: Epoch number (1-based).
            train_loss: Training loss for this epoch.
            val_loss: Validation loss for this epoch.
            learning_rate: Learning rate at this epoch.
            extra_metrics: Additional key-value pairs to log (e.g. accuracy, f1).
        """
        record: Dict[str, Any] = {
            "epoch": epoch,
            "train_loss": train_loss,
            "val_loss": val_loss,
            "learning_rate": learning_rate,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if extra_metrics:
            record.update(extra_metrics)

        try:
            with self._log_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record) + "\n")
            logger.debug("Recorded epoch %d train=%.4f val=%.4f", epoch, train_loss, val_loss)
        except OSError as exc:
            logger.error("Failed to write training log: %s", exc)

    def record_gradients(
        self,
        epoch: int,
        layer_gradients: Dict[str, List[float]],
    ) -> None:
        """Compute and store gradient statistics for a given epoch.

        Args:
            epoch: Epoch number.
            layer_gradients: Mapping of layer_name → list of gradient values.
        """
        stats: List[GradientStats] = []
        for layer_name, grads in layer_gradients.items():
            if not grads:
                continue
            abs_grads = [abs(g) for g in grads]
            mean_val = statistics.mean(abs_grads)
            std_val = statistics.pstdev(grads) if len(grads) > 1 else 0.0
            max_abs = max(abs_grads)
            stats.append(
                GradientStats(
                    layer_name=layer_name,
                    mean=round(mean_val, 8),
                    std=round(std_val, 8),
                    max_abs=round(max_abs, 8),
                    is_exploding=max_abs > _EXPLODING_THRESHOLD,
                    is_vanishing=mean_val < _VANISHING_THRESHOLD,
                )
            )
        self._gradient_log[epoch] = stats
        logger.debug("Recorded gradients epoch=%d layers=%d", epoch, len(stats))

    # ------------------------------------------------------------------
    # Loss curves
    # ------------------------------------------------------------------

    def get_loss_curve(self, last_n: Optional[int] = None) -> LossCurve:
        """Build the loss curve from the training log.

        Overfitting is detected when val_loss increased for 3 or more
        consecutive epochs while train_loss simultaneously decreased.

        Args:
            last_n: If provided, return only the last N epochs.

        Returns:
            A ``LossCurve`` instance.
        """
        records = self._read_log()
        if last_n is not None:
            records = records[-last_n:]

        epochs = [r["epoch"] for r in records]
        train_losses = [r.get("train_loss", 0.0) for r in records]
        val_losses = [r.get("val_loss", 0.0) for r in records]

        overfit = self._detect_overfitting(train_losses, val_losses)
        return LossCurve(
            epochs=epochs,
            train_loss=train_losses,
            val_loss=val_losses,
            overfitting_detected=overfit,
        )

    def _detect_overfitting(
        self,
        train_losses: List[float],
        val_losses: List[float],
    ) -> bool:
        """Return True if overfitting pattern detected.

        Overfitting = val_loss increased for _OVERFITTING_WINDOW consecutive epochs
        while train_loss decreased over the same window.

        Args:
            train_losses: Train loss series.
            val_losses: Validation loss series.

        Returns:
            True if overfitting detected.
        """
        n = len(train_losses)
        if n < _OVERFITTING_WINDOW + 1:
            return False

        for i in range(n - _OVERFITTING_WINDOW):
            window_end = i + _OVERFITTING_WINDOW
            val_increasing = all(
                val_losses[j + 1] > val_losses[j]
                for j in range(i, window_end)
            )
            train_decreasing = all(
                train_losses[j + 1] < train_losses[j]
                for j in range(i, window_end)
            )
            if val_increasing and train_decreasing:
                return True
        return False

    # ------------------------------------------------------------------
    # Gradient statistics
    # ------------------------------------------------------------------

    def get_gradient_stats(self, epoch: int) -> List[GradientStats]:
        """Return gradient statistics recorded for a specific epoch.

        Args:
            epoch: Epoch number.

        Returns:
            List of ``GradientStats``, one per recorded layer.
        """
        return self._gradient_log.get(epoch, [])

    # ------------------------------------------------------------------
    # Weight distribution
    # ------------------------------------------------------------------

    def get_weight_distribution(
        self, weights: Dict[str, List[float]]
    ) -> Dict[str, Dict[str, Any]]:
        """Compute distribution statistics for model weights per layer.

        Args:
            weights: Mapping of layer_name → list of weight values.

        Returns:
            Dict of {layer: {mean, std, min, max, percentiles: [p25, p50, p75]}}.
        """
        result: Dict[str, Dict[str, Any]] = {}
        for layer, vals in weights.items():
            if not vals:
                result[layer] = {"mean": 0, "std": 0, "min": 0, "max": 0, "percentiles": [0, 0, 0]}
                continue
            sorted_vals = sorted(vals)
            n = len(sorted_vals)
            mean = statistics.mean(vals)
            std = statistics.pstdev(vals) if n > 1 else 0.0
            p25 = sorted_vals[max(0, n // 4 - 1)]
            p50 = sorted_vals[max(0, n // 2 - 1)]
            p75 = sorted_vals[max(0, (3 * n) // 4 - 1)]
            result[layer] = {
                "mean": round(mean, 6),
                "std": round(std, 6),
                "min": round(sorted_vals[0], 6),
                "max": round(sorted_vals[-1], 6),
                "percentiles": [round(p25, 6), round(p50, 6), round(p75, 6)],
            }
        return result

    # ------------------------------------------------------------------
    # Confusion matrix
    # ------------------------------------------------------------------

    def get_confusion_matrix_data(
        self,
        y_true: List[Any],
        y_pred: List[Any],
        labels: List[Any],
    ) -> Dict[str, Any]:
        """Compute a confusion matrix and per-class classification metrics.

        Args:
            y_true: Ground-truth class labels.
            y_pred: Predicted class labels.
            labels: Ordered list of all class labels.

        Returns:
            Dict with: matrix (list[list[int]]), accuracy, per_class (dict with
            precision/recall/f1 per label).
        """
        n = len(labels)
        label_to_idx = {lbl: i for i, lbl in enumerate(labels)}

        # Build matrix
        matrix: List[List[int]] = [[0] * n for _ in range(n)]
        for t, p in zip(y_true, y_pred):
            ti = label_to_idx.get(t)
            pi = label_to_idx.get(p)
            if ti is not None and pi is not None:
                matrix[ti][pi] += 1

        total = sum(matrix[i][i] for i in range(n))
        grand_total = sum(sum(row) for row in matrix)
        accuracy = total / grand_total if grand_total else 0.0

        per_class: Dict[str, Dict[str, float]] = {}
        for i, label in enumerate(labels):
            tp = matrix[i][i]
            fp = sum(matrix[j][i] for j in range(n)) - tp
            fn = sum(matrix[i]) - tp
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (
                2 * precision * recall / (precision + recall)
                if (precision + recall) > 0
                else 0.0
            )
            per_class[str(label)] = {
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1": round(f1, 4),
                "support": int(sum(matrix[i])),
            }

        return {
            "matrix": matrix,
            "labels": [str(l) for l in labels],
            "accuracy": round(accuracy, 4),
            "per_class": per_class,
        }

    # ------------------------------------------------------------------
    # Dashboard payload
    # ------------------------------------------------------------------

    def get_dashboard_payload(self) -> Dict[str, Any]:
        """Serialize all training visualization data for the dashboard API.

        Reads from the JSONL log — no ML dependencies required.

        Returns:
            Dict ready to serve from ``/api/training/viz``.
        """
        records = self._read_log()
        loss_curve = self.get_loss_curve()

        # Aggregate gradient data for all logged epochs
        gradient_summary: List[Dict[str, Any]] = []
        for epoch, stats in sorted(self._gradient_log.items()):
            gradient_summary.append(
                {
                    "epoch": epoch,
                    "layers": [asdict(s) for s in stats],
                }
            )

        # Recent learning rate trend
        lr_trend = [
            {"epoch": r["epoch"], "lr": r.get("learning_rate", 0.0)}
            for r in records[-50:]
        ]

        # Extra metrics (accuracy, f1, etc.) if logged
        extra_keys = set()
        for r in records:
            extra_keys.update(k for k in r if k not in {"epoch", "train_loss", "val_loss", "learning_rate", "timestamp"})

        extra_series: Dict[str, List[Any]] = {k: [] for k in extra_keys}
        for r in records:
            for k in extra_keys:
                extra_series[k].append(r.get(k))

        return {
            "loss_curve": asdict(loss_curve),
            "gradient_history": gradient_summary,
            "lr_trend": lr_trend,
            "extra_metrics": extra_series,
            "total_epochs": len(records),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_live_data(self, last_n_epochs: int = 50) -> Dict[str, Any]:
        """Return a lightweight payload for real-time dashboard polling.

        Args:
            last_n_epochs: Number of most recent epochs to include.

        Returns:
            Dict with loss curves, lr trend, and overfitting flag.
        """
        records = self._read_log()
        recent = records[-last_n_epochs:]

        epochs = [r["epoch"] for r in recent]
        train_losses = [r.get("train_loss", 0.0) for r in recent]
        val_losses = [r.get("val_loss", 0.0) for r in recent]
        lr_trend = [r.get("learning_rate", 0.0) for r in recent]
        overfit = self._detect_overfitting(train_losses, val_losses)

        return {
            "epochs": epochs,
            "train_loss": train_losses,
            "val_loss": val_losses,
            "learning_rate": lr_trend,
            "overfitting_detected": overfit,
            "epoch_count": len(records),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _read_log(self) -> List[Dict[str, Any]]:
        """Read and parse all records from the JSONL training log.

        Returns:
            List of record dicts, ordered chronologically.
        """
        if not self._log_path.is_file():
            return []
        records: List[Dict[str, Any]] = []
        try:
            for line in self._log_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        except OSError as exc:
            logger.warning("Failed to read training log: %s", exc)
        return records
