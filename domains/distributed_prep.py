#!/usr/bin/env python3
"""Preparation utilities for distributed training on multiple GPUs or machines.

Detects available GPUs, generates DDP initialization code, partitions datasets,
estimates per-GPU memory requirements, and patches training scripts with the
necessary distributed boilerplate. Mac Studio support uses the ``gloo`` backend
with MPS device.
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional

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
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_MASTER_ADDR: str = "localhost"
_DEFAULT_MASTER_PORT: int = 29500
_AVG_SAMPLE_BYTES: int = 512  # heuristic average bytes per training sample

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class DistributedConfig:
    """Configuration for a distributed training process group.

    Attributes:
        world_size: Total number of processes (GPUs or ranks).
        rank: Global rank of this process.
        local_rank: Local rank within the node.
        backend: PyTorch distributed backend ("nccl", "gloo", "mpi").
        init_method: URL for process group initialization.
        master_addr: Hostname/IP of the master node.
        master_port: Port used by the master node.
    """

    world_size: int
    rank: int
    local_rank: int
    backend: str
    init_method: str
    master_addr: str
    master_port: int


@dataclass
class DataPartition:
    """A contiguous slice of a dataset assigned to one training rank.

    Attributes:
        rank: Rank this partition belongs to.
        total_ranks: Total number of ranks in the group.
        indices: Dataset sample indices for this rank.
        dataset_size: Total dataset size.
    """

    rank: int
    total_ranks: int
    indices: List[int]
    dataset_size: int


# ---------------------------------------------------------------------------
# DistributedPrep
# ---------------------------------------------------------------------------


class DistributedPrep:
    """Utilities for configuring and launching distributed PyTorch training.

    Detects hardware (CUDA GPUs or Apple MPS), generates DDP boilerplate,
    partitions datasets evenly across ranks, and estimates memory requirements.

    Example::

        prep = DistributedPrep()
        n_gpus = prep.detect_gpus()
        config = prep.create_config(world_size=n_gpus)
        code = prep.get_ddp_setup_code(config)
        print(code)
    """

    def __init__(self) -> None:
        """Initialise DistributedPrep."""
        logger.debug("DistributedPrep initialised torch_available=%s", _TORCH_AVAILABLE)

    # ------------------------------------------------------------------
    # GPU detection
    # ------------------------------------------------------------------

    def detect_gpus(self) -> int:
        """Return the number of available CUDA GPUs.

        Uses ``torch.cuda.device_count()`` if torch is available,
        otherwise falls back to ``nvidia-smi``.

        Returns:
            Number of GPUs (0 if none detected or CUDA unavailable).
        """
        if _TORCH_AVAILABLE:
            try:
                count = _torch.cuda.device_count()
                logger.debug("torch.cuda.device_count() = %d", count)
                return count
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning("torch.cuda.device_count() failed: %s", exc)

        # Fallback: nvidia-smi
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
                logger.debug("nvidia-smi detected %d GPU(s)", len(lines))
                return len(lines)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        logger.debug("No GPUs detected")
        return 0

    # ------------------------------------------------------------------
    # Config creation
    # ------------------------------------------------------------------

    def create_config(
        self,
        world_size: Optional[int] = None,
        backend: str = "nccl",
    ) -> DistributedConfig:
        """Create a distributed training configuration.

        Reads ``MASTER_ADDR`` and ``MASTER_PORT`` from environment if set.
        Defaults ``world_size`` to ``detect_gpus()`` or 1 if no GPUs found.

        Args:
            world_size: Override world size; defaults to GPU count (min 1).
            backend: PyTorch distributed backend.

        Returns:
            A ``DistributedConfig`` for this node.
        """
        if world_size is None:
            world_size = max(1, self.detect_gpus())

        master_addr = os.environ.get("MASTER_ADDR", _DEFAULT_MASTER_ADDR)
        master_port = int(os.environ.get("MASTER_PORT", str(_DEFAULT_MASTER_PORT)))
        rank = int(os.environ.get("RANK", "0"))
        local_rank = int(os.environ.get("LOCAL_RANK", "0"))
        init_method = f"env://"

        config = DistributedConfig(
            world_size=world_size,
            rank=rank,
            local_rank=local_rank,
            backend=backend,
            init_method=init_method,
            master_addr=master_addr,
            master_port=master_port,
        )
        logger.info(
            "DistributedConfig: world_size=%d backend=%s addr=%s:%d",
            world_size,
            backend,
            master_addr,
            master_port,
        )
        return config

    # ------------------------------------------------------------------
    # Dataset partitioning
    # ------------------------------------------------------------------

    def partition_dataset(
        self,
        dataset_size: int,
        world_size: int,
        rank: int,
    ) -> DataPartition:
        """Partition a dataset into even slices for distributed training.

        Splits the dataset as evenly as possible; the last rank receives
        any remainder samples.

        Args:
            dataset_size: Total number of samples in the dataset.
            world_size: Number of ranks.
            rank: Zero-based rank of this process.

        Returns:
            A ``DataPartition`` containing this rank's sample indices.
        """
        if world_size <= 0:
            raise ValueError(f"world_size must be > 0, got {world_size}")
        if rank < 0 or rank >= world_size:
            raise ValueError(f"rank must be in [0, {world_size - 1}], got {rank}")

        base_size = dataset_size // world_size
        remainder = dataset_size % world_size

        start = rank * base_size
        end = start + base_size

        # Last rank absorbs remainder
        if rank == world_size - 1:
            end += remainder

        indices = list(range(start, end))
        logger.debug(
            "Partition rank=%d/%d: indices[%d:%d] (%d samples)",
            rank,
            world_size,
            start,
            end,
            len(indices),
        )
        return DataPartition(
            rank=rank,
            total_ranks=world_size,
            indices=indices,
            dataset_size=dataset_size,
        )

    # ------------------------------------------------------------------
    # Code generation
    # ------------------------------------------------------------------

    def get_ddp_setup_code(self, config: DistributedConfig) -> str:
        """Return a Python code snippet that initializes torch DDP.

        Args:
            config: Distributed training configuration.

        Returns:
            Importable Python code string.
        """
        return f"""\
import os
import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP

# ---- DDP Initialization ----
os.environ["MASTER_ADDR"] = "{config.master_addr}"
os.environ["MASTER_PORT"] = "{config.master_port}"
os.environ["RANK"] = str({config.rank})
os.environ["LOCAL_RANK"] = str({config.local_rank})
os.environ["WORLD_SIZE"] = str({config.world_size})

dist.init_process_group(
    backend="{config.backend}",
    init_method="{config.init_method}",
    world_size={config.world_size},
    rank={config.rank},
)

local_rank = int(os.environ.get("LOCAL_RANK", 0))
device = torch.device("cuda", local_rank) if torch.cuda.is_available() else torch.device("cpu")
torch.cuda.set_device(local_rank)

# Wrap model:
# model = DDP(model.to(device), device_ids=[local_rank])
"""

    def get_launch_command(self, script: str, n_gpus: int) -> str:
        """Return the recommended torchrun launch command.

        Prefers ``torchrun`` (PyTorch >= 1.10); falls back to
        ``python -m torch.distributed.launch`` for older installations.

        Args:
            script: Path to the training script.
            n_gpus: Number of GPUs per node.

        Returns:
            Shell command string.
        """
        n = max(1, n_gpus)
        # Check torchrun availability
        try:
            result = subprocess.run(
                ["torchrun", "--version"],
                capture_output=True,
                timeout=5,
            )
            use_torchrun = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            use_torchrun = False

        if use_torchrun:
            return f"torchrun --nproc_per_node={n} {script}"
        return f"python -m torch.distributed.launch --nproc_per_node={n} {script}"

    # ------------------------------------------------------------------
    # Memory estimation
    # ------------------------------------------------------------------

    def estimate_memory_per_gpu(
        self,
        model_params: int,
        batch_size: int,
        dtype_bytes: int = 4,
    ) -> float:
        """Estimate GPU memory required per rank in gigabytes.

        Heuristic: (model_params * dtype_bytes + batch_size * avg_sample_bytes) / 1e9
        Adds a 20% overhead factor for optimizer state and activations.

        Args:
            model_params: Total number of model parameters.
            batch_size: Per-rank batch size.
            dtype_bytes: Bytes per parameter (4 = float32, 2 = float16/bfloat16).

        Returns:
            Estimated memory in GB.
        """
        model_bytes = model_params * dtype_bytes
        sample_bytes = batch_size * _AVG_SAMPLE_BYTES
        total_bytes = (model_bytes + sample_bytes) * 1.2  # 20% overhead
        gb = total_bytes / 1e9
        logger.debug(
            "estimate_memory_per_gpu: params=%d batch=%d dtype=%d → %.3fGB",
            model_params,
            batch_size,
            dtype_bytes,
            gb,
        )
        return round(gb, 3)

    # ------------------------------------------------------------------
    # Mac Studio config
    # ------------------------------------------------------------------

    def get_mac_studio_config(self) -> DistributedConfig:
        """Return a distributed config optimised for Apple Silicon Mac Studio.

        Uses gloo backend (compatible with MPS) with world_size=1.

        Returns:
            A single-rank ``DistributedConfig`` for MPS.
        """
        config = DistributedConfig(
            world_size=1,
            rank=0,
            local_rank=0,
            backend="gloo",
            init_method="env://",
            master_addr=_DEFAULT_MASTER_ADDR,
            master_port=_DEFAULT_MASTER_PORT,
        )
        logger.info("Mac Studio config: backend=gloo device=mps world_size=1")
        return config

    # ------------------------------------------------------------------
    # Script patching
    # ------------------------------------------------------------------

    def generate_training_script_patches(self, original_script: str) -> str:
        """Patch a training script to support DDP distributed training.

        Inserts:
        1. DDP import block at the top (after existing imports).
        2. ``dist.init_process_group(...)`` call before the training loop.
        3. Model wrapping: ``model = DDP(model, device_ids=[local_rank])``.
        4. Distributed sampler usage for the DataLoader.

        Args:
            original_script: Original training script as a string.

        Returns:
            Patched script string.
        """
        ddp_imports = """\
# --- DDP imports (auto-patched by DistributedPrep) ---
import os
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data.distributed import DistributedSampler
# -------------------------------------------------------
"""
        ddp_init = """\
# --- DDP initialization (auto-patched) ---
local_rank = int(os.environ.get("LOCAL_RANK", 0))
rank = int(os.environ.get("RANK", 0))
world_size = int(os.environ.get("WORLD_SIZE", 1))
if world_size > 1:
    dist.init_process_group(backend="nccl", init_method="env://",
                             world_size=world_size, rank=rank)
    torch.cuda.set_device(local_rank)
device = torch.device("cuda", local_rank) if torch.cuda.is_available() else torch.device("cpu")
# ------------------------------------------
"""
        model_wrap = """\
# --- DDP model wrap (auto-patched) ---
if world_size > 1:
    model = DDP(model.to(device), device_ids=[local_rank], output_device=local_rank)
else:
    model = model.to(device)
# -------------------------------------
"""
        sampler_patch = """\
# --- Distributed sampler (auto-patched) ---
_ddp_sampler = DistributedSampler(dataset, num_replicas=world_size, rank=rank) if world_size > 1 else None
# Replace shuffle=True with sampler=_ddp_sampler in your DataLoader call
# ------------------------------------------
"""

        # Insert DDP imports after last import line
        lines = original_script.splitlines(keepends=True)
        last_import_idx = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                last_import_idx = i

        lines.insert(last_import_idx + 1, ddp_imports)

        # Find a likely position for init (after all imports, before first function/class or training code)
        # Insert DDP init block near top of script body
        init_pos = last_import_idx + 2  # just after imports + ddp import block
        lines.insert(init_pos, ddp_init)

        # Append model wrap and sampler hints at the end as comments/stubs
        lines.append("\n" + model_wrap)
        lines.append("\n" + sampler_patch)

        patched = "".join(lines)
        logger.info("Patched training script: added DDP init, model wrap, and sampler stub")
        return patched
