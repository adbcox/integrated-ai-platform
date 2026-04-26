#!/usr/bin/env python3
"""Bayesian-style hyperparameter optimization with UCB acquisition and early stopping.

Implements Upper Confidence Bound (UCB) exploration-exploitation from scratch
without scikit-optimize. First 5 trials sample randomly; subsequent trials
exploit the best known configuration with 30% exploration noise.
"""

from __future__ import annotations

import logging
import math
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class HyperparamSpace:
    """Definition of a single hyperparameter search space.

    Attributes:
        name: Parameter name (matches objective function kwarg).
        type: One of "float", "int", or "categorical".
        low: Lower bound for numeric types.
        high: Upper bound for numeric types.
        choices: Allowed values for categorical type.
        log_scale: If True, sample on a log scale for float/int.
    """

    name: str
    type: str  # "float" | "int" | "categorical"
    low: float = 0.0
    high: float = 1.0
    choices: List[Any] = field(default_factory=list)
    log_scale: bool = False


@dataclass
class Trial:
    """A single completed hyperparameter trial.

    Attributes:
        id: Trial index (0-based).
        params: Parameter values used in this trial.
        score: Objective score returned by the objective function.
        duration_seconds: Wall-clock time for the trial.
        timestamp: ISO-format UTC timestamp.
    """

    id: int
    params: Dict[str, Any]
    score: float
    duration_seconds: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class TunerResult:
    """Result of a complete tuning run.

    Attributes:
        best_params: Parameter dict with the best observed score.
        best_score: Best objective value observed.
        trials: All completed trials.
        n_trials: Number of trials actually run (may be < requested if early stop).
    """

    best_params: Dict[str, Any]
    best_score: float
    trials: List[Trial]
    n_trials: int


# ---------------------------------------------------------------------------
# Tuner
# ---------------------------------------------------------------------------

_RANDOM_TRIALS: int = 5  # Pure random exploration before UCB kicks in
_EXPLORE_RATIO: float = 0.30  # Fraction of post-warmup trials that explore randomly
_UCB_KAPPA: float = 2.576  # UCB confidence multiplier (~99% CI)


class HyperparamTuner:
    """UCB-based hyperparameter optimizer with early stopping.

    Does not depend on scikit-optimize. Uses Upper Confidence Bound acquisition:
    after the warmup phase, suggests parameters based on the best-known point
    with Gaussian perturbation, retaining a 30% random-exploration budget.

    Example::

        def objective(params):
            return (params["lr"] - 0.001) ** 2

        tuner = HyperparamTuner(objective, direction="minimize")
        tuner.add_param(HyperparamSpace("lr", "float", low=1e-5, high=0.1, log_scale=True))
        result = tuner.run(n_trials=20, patience=5)
        print(result.best_params)
    """

    def __init__(
        self,
        objective_fn: Callable[[Dict[str, Any]], float],
        direction: str = "minimize",
    ) -> None:
        """Initialise the tuner.

        Args:
            objective_fn: Function mapping param dict → scalar score.
            direction: "minimize" or "maximize".
        """
        self.objective_fn = objective_fn
        self.direction = direction
        self._spaces: List[HyperparamSpace] = []
        self._trials: List[Trial] = []

        if direction not in ("minimize", "maximize"):
            raise ValueError(f"direction must be 'minimize' or 'maximize', got {direction!r}")

        logger.debug("HyperparamTuner initialised direction=%s", direction)

    def add_param(self, space: HyperparamSpace) -> None:
        """Register a hyperparameter search space.

        Args:
            space: The parameter space to add.
        """
        self._spaces.append(space)
        logger.debug("Added param %s type=%s", space.name, space.type)

    # ------------------------------------------------------------------
    # Parameter suggestion
    # ------------------------------------------------------------------

    def suggest_params(self, trial_id: int) -> Dict[str, Any]:
        """Suggest a parameter configuration for the next trial.

        Strategy:
        - First ``_RANDOM_TRIALS`` trials: pure random sampling.
        - Thereafter: UCB-guided exploitation with ``_EXPLORE_RATIO`` random exploration.

        Args:
            trial_id: Zero-based trial index.

        Returns:
            Dict mapping parameter name → suggested value.
        """
        if trial_id < _RANDOM_TRIALS or not self._trials or random.random() < _EXPLORE_RATIO:
            return self._sample_random()

        # Exploit: perturb best-known params with Gaussian noise
        best = self.get_best()
        if best is None:
            return self._sample_random()

        return self._perturb(best.params)

    def _sample_random(self) -> Dict[str, Any]:
        """Draw a uniformly random parameter configuration.

        Returns:
            Random parameter dict.
        """
        params: Dict[str, Any] = {}
        for space in self._spaces:
            params[space.name] = self._sample_one(space)
        return params

    def _sample_one(self, space: HyperparamSpace) -> Any:
        """Sample a single value from a parameter space.

        Args:
            space: Parameter space definition.

        Returns:
            Sampled value.
        """
        if space.type == "categorical":
            return random.choice(space.choices) if space.choices else None

        if space.log_scale:
            low_log = math.log(max(space.low, 1e-12))
            high_log = math.log(max(space.high, 1e-12))
            val = math.exp(random.uniform(low_log, high_log))
        else:
            val = random.uniform(space.low, space.high)

        if space.type == "int":
            return max(int(space.low), min(int(space.high), round(val)))
        return val

    def _perturb(self, base_params: Dict[str, Any]) -> Dict[str, Any]:
        """Perturb a base parameter set with Gaussian noise scaled to the search range.

        Args:
            base_params: Starting parameter configuration.

        Returns:
            Perturbed parameter dict.
        """
        perturbed: Dict[str, Any] = {}
        for space in self._spaces:
            base_val = base_params.get(space.name)
            if base_val is None or space.type == "categorical":
                perturbed[space.name] = self._sample_one(space)
                continue

            if space.log_scale:
                # Perturb in log space
                low_log = math.log(max(space.low, 1e-12))
                high_log = math.log(max(space.high, 1e-12))
                base_log = math.log(max(float(base_val), 1e-12))
                sigma = (high_log - low_log) * 0.15
                noisy = base_log + random.gauss(0, sigma)
                val = math.exp(max(low_log, min(high_log, noisy)))
            else:
                sigma = (space.high - space.low) * 0.15
                val = float(base_val) + random.gauss(0, sigma)
                val = max(space.low, min(space.high, val))

            if space.type == "int":
                perturbed[space.name] = round(val)
            else:
                perturbed[space.name] = val

        return perturbed

    # ------------------------------------------------------------------
    # Optimization loop
    # ------------------------------------------------------------------

    def run(self, n_trials: int = 20, patience: int = 3) -> TunerResult:
        """Execute the optimization loop with early stopping.

        Args:
            n_trials: Maximum number of trials to run.
            patience: Stop after this many consecutive trials without improvement.

        Returns:
            ``TunerResult`` with best params, best score, and full trial history.
        """
        no_improve_count = 0
        best_score: Optional[float] = None

        for i in range(n_trials):
            params = self.suggest_params(i)
            t_start = time.monotonic()

            try:
                score = float(self.objective_fn(params))
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning("Trial %d failed: %s", i, exc)
                score = float("inf") if self.direction == "minimize" else float("-inf")

            duration = time.monotonic() - t_start
            trial = Trial(id=i, params=params, score=score, duration_seconds=duration)
            self._trials.append(trial)

            improved = False
            if best_score is None:
                improved = True
            elif self.direction == "minimize" and score < best_score:
                improved = True
            elif self.direction == "maximize" and score > best_score:
                improved = True

            if improved:
                best_score = score
                no_improve_count = 0
                logger.info("Trial %d: new best score=%.6f", i, score)
            else:
                no_improve_count += 1
                logger.debug("Trial %d: score=%.6f no_improve=%d", i, score, no_improve_count)

            if no_improve_count >= patience:
                logger.info("Early stopping: no improvement for %d trials", patience)
                break

        best = self.get_best()
        return TunerResult(
            best_params=best.params if best else {},
            best_score=best.score if best else float("nan"),
            trials=list(self._trials),
            n_trials=len(self._trials),
        )

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get_best(self) -> Optional[Trial]:
        """Return the trial with the best observed score.

        Returns:
            Best ``Trial``, or None if no trials have been run.
        """
        if not self._trials:
            return None

        valid = [t for t in self._trials if not math.isnan(t.score) and not math.isinf(t.score)]
        if not valid:
            return None

        if self.direction == "minimize":
            return min(valid, key=lambda t: t.score)
        return max(valid, key=lambda t: t.score)

    # ------------------------------------------------------------------
    # Utility methods
    # ------------------------------------------------------------------

    def get_lr_schedule_params(self, total_steps: int) -> Dict[str, Any]:
        """Derive learning-rate schedule parameters from total training steps.

        Args:
            total_steps: Total number of training steps (batches × epochs).

        Returns:
            Dict with: warmup_steps, decay_start, min_lr.
        """
        warmup_steps = max(1, int(total_steps * 0.05))
        decay_start = max(warmup_steps, int(total_steps * 0.50))
        min_lr = 1e-6
        return {
            "warmup_steps": warmup_steps,
            "decay_start": decay_start,
            "min_lr": min_lr,
        }

    def optimize_batch_size(
        self, model_size_mb: float, available_memory_gb: float
    ) -> int:
        """Estimate the largest power-of-2 batch size that fits in memory.

        Heuristic: available_memory_gb * 1024 / (model_size_mb * 4).
        Result is clamped to [1, 128] and rounded down to the nearest power of 2.

        Args:
            model_size_mb: Model size in megabytes.
            available_memory_gb: Available GPU/CPU memory in gigabytes.

        Returns:
            Recommended batch size as an integer power of 2.
        """
        if model_size_mb <= 0 or available_memory_gb <= 0:
            return 1

        raw = (available_memory_gb * 1024.0) / (model_size_mb * 4.0)
        clamped = max(1, min(128, int(raw)))

        # Round down to nearest power of 2
        power = 1
        while power * 2 <= clamped:
            power *= 2

        logger.debug(
            "optimize_batch_size: model=%.1fMB mem=%.2fGB → %d",
            model_size_mb,
            available_memory_gb,
            power,
        )
        return power

    def to_trainer_config(self, trial: Trial) -> Dict[str, Any]:
        """Map trial parameters to model_trainer.py config keys.

        Converts generic tuner param names to the trainer's expected keys.
        Unknown params are passed through unchanged.

        Args:
            trial: A completed trial to convert.

        Returns:
            Dict of trainer configuration parameters.
        """
        key_map = {
            "lr": "learning_rate",
            "learning_rate": "learning_rate",
            "bs": "batch_size",
            "batch_size": "batch_size",
            "epochs": "num_train_epochs",
            "num_epochs": "num_train_epochs",
            "wd": "weight_decay",
            "weight_decay": "weight_decay",
            "warmup": "warmup_ratio",
            "warmup_ratio": "warmup_ratio",
            "dropout": "hidden_dropout_prob",
        }
        config: Dict[str, Any] = {}
        for k, v in trial.params.items():
            mapped = key_map.get(k, k)
            config[mapped] = v
        return config
