"""Observer pattern — event-driven notification between loosely coupled objects.

Use when: one object's state change needs to notify multiple dependents
         without tight coupling (metrics collection, event streaming, logging).
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any


class Event:
    def __init__(self, name: str, data: Any = None) -> None:
        self.name = name
        self.data = data


class Observer(ABC):
    @abstractmethod
    def update(self, event: Event) -> None: ...


class Observable:
    def __init__(self) -> None:
        self._observers: dict[str, list[Observer]] = {}

    def subscribe(self, event_name: str, observer: Observer) -> None:
        self._observers.setdefault(event_name, []).append(observer)

    def unsubscribe(self, event_name: str, observer: Observer) -> None:
        self._observers.get(event_name, []).remove(observer)

    def emit(self, event: Event) -> None:
        for obs in self._observers.get(event.name, []):
            obs.update(event)
        for obs in self._observers.get("*", []):  # wildcard
            obs.update(event)


# ── Concrete example ────────────────────────────────────────────────────────

class MetricsCollector(Observer):
    def __init__(self) -> None:
        self.events: list[Event] = []

    def update(self, event: Event) -> None:
        self.events.append(event)
        print(f"[metrics] {event.name}: {event.data}")


class TaskRunner(Observable):
    def run(self, task_name: str) -> bool:
        self.emit(Event("task.started", {"task": task_name}))
        # ... do work ...
        success = True
        self.emit(Event("task.completed", {"task": task_name, "success": success}))
        return success


if __name__ == "__main__":
    runner = TaskRunner()
    metrics = MetricsCollector()
    runner.subscribe("task.started", metrics)
    runner.subscribe("task.completed", metrics)
    runner.run("build_index")
