"""Service layer pattern — business logic separated from HTTP/CLI/persistence.

Use when: same logic needs to be called from API endpoints, CLI tools, and
         tests without duplicating code (task management, media processing).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path
import json


@dataclass
class ServiceResult:
    success: bool
    data: dict = field(default_factory=dict)
    error: str = ""

    @classmethod
    def ok(cls, **data) -> "ServiceResult":
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str) -> "ServiceResult":
        return cls(success=False, error=error)


class TaskService:
    """Business logic for task management — no HTTP, no CLI, no storage details."""

    def __init__(self, storage_path: Path) -> None:
        self.storage_path = storage_path
        self._tasks: dict[str, dict] = self._load()

    def _load(self) -> dict:
        if self.storage_path.exists():
            return json.loads(self.storage_path.read_text())
        return {}

    def _save(self) -> None:
        self.storage_path.write_text(json.dumps(self._tasks, indent=2))

    def create(self, title: str, category: str) -> ServiceResult:
        if not title.strip():
            return ServiceResult.fail("title cannot be empty")
        import uuid
        task_id = str(uuid.uuid4())[:8]
        self._tasks[task_id] = {"title": title, "category": category, "status": "pending"}
        self._save()
        return ServiceResult.ok(id=task_id, task=self._tasks[task_id])

    def complete(self, task_id: str) -> ServiceResult:
        task = self._tasks.get(task_id)
        if not task:
            return ServiceResult.fail(f"task {task_id} not found")
        task["status"] = "completed"
        self._save()
        return ServiceResult.ok(id=task_id, task=task)

    def list_pending(self) -> list[dict]:
        return [{"id": k, **v} for k, v in self._tasks.items() if v.get("status") == "pending"]


# ── Thin API layer (just wires HTTP to service) ─────────────────────────────

def make_api(service: TaskService):
    """FastAPI app — all logic delegates to TaskService."""
    try:
        from fastapi import FastAPI, HTTPException
        app = FastAPI()

        @app.post("/tasks")
        def create_task(title: str, category: str = "CORE"):
            result = service.create(title, category)
            if not result.success:
                raise HTTPException(400, result.error)
            return result.data

        @app.get("/tasks")
        def list_tasks():
            return service.list_pending()

        return app
    except ImportError:
        return None
