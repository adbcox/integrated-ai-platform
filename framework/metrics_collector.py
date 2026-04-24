import time
from dataclasses import dataclass
from typing import Dict, Any

@dataclass(frozen=True)
class TaskMetrics:
    task_id: str
    start_time: float
    end_time: float
    duration: float
    success: bool
    error_type: str = None
    tokens_used: int = 0
    exit_code: int = 0

@dataclass(frozen=True)
class ModelMetrics:
    model_name: str
    inference_time: float
    accuracy: float
    precision: float
    recall: float

@dataclass(frozen=True)
class SystemMetrics:
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_usage: float

def collect_task_metrics(task_id: str, success: bool, error_type: str = None, tokens_used: int = 0, exit_code: int = 0) -> TaskMetrics:
    start_time = time.time()
    end_time = time.time()
    duration = end_time - start_time
    return TaskMetrics(
        task_id=task_id,
        start_time=start_time,
        end_time=end_time,
        duration=duration,
        success=success,
        error_type=error_type,
        tokens_used=tokens_used,
        exit_code=exit_code
    )

def collect_model_metrics(model_name: str, inference_time: float, accuracy: float, precision: float, recall: float) -> ModelMetrics:
    return ModelMetrics(
        model_name=model_name,
        inference_time=inference_time,
        accuracy=accuracy,
        precision=precision,
        recall=recall
    )

def collect_system_metrics() -> SystemMetrics:
    # Placeholder for actual system metrics collection logic
    cpu_usage = 0.5  # Example value
    memory_usage = 2.3  # Example value
    disk_usage = 1.8  # Example value
    network_usage = 0.7  # Example value
    return SystemMetrics(
        cpu_usage=cpu_usage,
        memory_usage=memory_usage,
        disk_usage=disk_usage,
        network_usage=network_usage
    )

def log_task_metrics(metrics: TaskMetrics) -> None:
    print(f"Task Metrics - ID: {metrics.task_id}, Duration: {metrics.duration:.2f}s, Success: {metrics.success}, Error Type: {metrics.error_type}")

def log_model_metrics(metrics: ModelMetrics) -> None:
    print(f"Model Metrics - Name: {metrics.model_name}, Inference Time: {metrics.inference_time:.2f}s, Accuracy: {metrics.accuracy:.2f}, Precision: {metrics.precision:.2f}, Recall: {metrics.recall:.2f}")

def log_system_metrics(metrics: SystemMetrics) -> None:
    print(f"System Metrics - CPU Usage: {metrics.cpu_usage:.2f}, Memory Usage: {metrics.memory_usage:.2f}, Disk Usage: {metrics.disk_usage:.2f}, Network Usage: {metrics.network_usage:.2f}")
