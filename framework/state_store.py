"""Artifact/state persistence for scheduler, workers, traces, and outcomes."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .compat import UTC
from .job_schema import Job, parse_job


class StateStore:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.jobs_dir = self.root / "jobs"
        self.results_dir = self.root / "results"
        self.traces_dir = self.root / "traces"
        self.queue_dir = self.root / "queue"
        self.learning_dir = self.root / "learning"
        self.dead_letter_dir = self.root / "dead_letter"
        for path in (
            self.jobs_dir,
            self.results_dir,
            self.traces_dir,
            self.queue_dir,
            self.learning_dir,
            self.dead_letter_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError as e:
            raise RuntimeError(f"Failed to write JSON to {path}: {e}") from e

    def _append_jsonl(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False)
            handle.write("\n")

    def _read_jsonl(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        rows: list[dict[str, Any]] = []
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict):
                    rows.append(payload)
        return rows

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

    def list_jobs(self) -> list[Job]:
        jobs: list[Job] = []
        for path in sorted(self.jobs_dir.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if not isinstance(payload, dict):
                continue
            try:
                jobs.append(parse_job(payload))
            except Exception:
                continue
        return jobs

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

    def save_queue_snapshot(self, payload: dict[str, Any]) -> Path:
        stamped = {
            "saved_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            **payload,
        }
        path = self.queue_dir / "snapshot.json"
        self._write_json(path, stamped)
        return path

    def append_learning_event(self, payload: dict[str, Any]) -> None:
        row = {
            "timestamp_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            **payload,
        }
        self._append_jsonl(self.learning_dir / "events.jsonl", row)

    def read_learning_events(self) -> list[dict[str, Any]]:
        return self._read_jsonl(self.learning_dir / "events.jsonl")

    def append_dead_letter_event(self, payload: dict[str, Any]) -> None:
        row = {
            "timestamp_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            **payload,
        }
        self._append_jsonl(self.dead_letter_dir / "events.jsonl", row)

    def save_dead_letter_record(self, *, job: Job, result_payload: dict[str, Any], reason: str) -> Path:
        path = self.dead_letter_dir / f"{job.job_id}.json"
        payload = {
            "saved_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "reason": reason,
            "job": job.to_dict(),
            "result": result_payload,
        }
        self._write_json(path, payload)
        self.append_dead_letter_event(
            {
                "kind": "dead_letter_saved",
                "job_id": job.job_id,
                "task_class": job.task_class.value,
                "reason": reason,
                "final_lifecycle": job.lifecycle.value,
                "dead_letter_path": str(path),
            }
        )
        return path
