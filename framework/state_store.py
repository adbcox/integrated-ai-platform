"""Artifact/state persistence for scheduler, workers, traces, and outcomes."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .job_schema import Job, parse_job


class StateStore:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.jobs_dir = self.root / "jobs"
        self.results_dir = self.root / "results"
        self.traces_dir = self.root / "traces"
        self.queue_dir = self.root / "queue"
        self.learning_dir = self.root / "learning"
        for path in (self.jobs_dir, self.results_dir, self.traces_dir, self.queue_dir, self.learning_dir):
            path.mkdir(parents=True, exist_ok=True)

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _append_jsonl(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False)
            handle.write("\n")

    def save_job(self, job: Job) -> None:
        self._write_json(self.jobs_dir / f"{job.job_id}.json", job.to_dict())

    def load_job(self, job_id: str) -> Job | None:
        path = self.jobs_dir / f"{job_id}.json"
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict):
            return None
        return parse_job(payload)

    def save_result(self, job_id: str, payload: dict[str, Any]) -> Path:
        path = self.results_dir / f"{job_id}.json"
        stamped = {
            "saved_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            **payload,
        }
        self._write_json(path, stamped)
        return path

    def append_trace(self, payload: dict[str, Any]) -> None:
        row = {
            "timestamp_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            **payload,
        }
        self._append_jsonl(self.traces_dir / "events.jsonl", row)

    def append_queue_event(self, payload: dict[str, Any]) -> None:
        row = {
            "timestamp_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            **payload,
        }
        self._append_jsonl(self.queue_dir / "events.jsonl", row)

    def append_learning_event(self, payload: dict[str, Any]) -> None:
        row = {
            "timestamp_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            **payload,
        }
        self._append_jsonl(self.learning_dir / "events.jsonl", row)
