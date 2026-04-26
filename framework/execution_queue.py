#!/usr/bin/env python3
"""SQLite-backed execution queue for roadmap task plans."""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger(__name__)

_REPO = Path(__file__).parent.parent
_DEFAULT_DB = _REPO / "data" / "execution_queue.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id           TEXT PRIMARY KEY,
    plan_id      TEXT NOT NULL,
    item_id      TEXT NOT NULL,
    subtask_id   TEXT NOT NULL,
    title        TEXT NOT NULL,
    description  TEXT,
    target_files TEXT,      -- JSON array
    engine       TEXT,      -- claimed by which engine
    status       TEXT NOT NULL DEFAULT 'pending',
    priority     TEXT NOT NULL DEFAULT 'medium',
    created_at   REAL NOT NULL,
    claimed_at   REAL,
    completed_at REAL,
    error        TEXT,
    result       TEXT        -- JSON result blob
);

CREATE INDEX IF NOT EXISTS idx_tasks_status   ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_item_id  ON tasks(item_id);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority, created_at);
"""

_PRIORITY_ORDER = {"urgent": 0, "high": 1, "medium": 2, "low": 3, "none": 4}


class ExecutionQueue:
    """Persistent task queue backed by SQLite.

    Thread-safe for single-host use (SQLite WAL mode).
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = Path(db_path or _DEFAULT_DB)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    # ── Write operations ─────────────────────────────────────────────────────

    def enqueue_plan(self, plan: Dict, priority: str = "medium") -> List[str]:
        """Insert all subtasks from an execution plan. Returns list of task IDs."""
        item_id = plan.get("item_id", "UNKNOWN")
        plan_id = str(uuid.uuid4())
        task_ids: List[str] = []
        now = time.time()

        subtasks = plan.get("subtasks", [])
        if not subtasks:
            log.warning("enqueue_plan: plan %s has no subtasks", item_id)
            return []

        priority = plan.get("priority", priority) or priority

        with self._conn:
            for st in subtasks:
                task_id = str(uuid.uuid4())
                self._conn.execute(
                    """INSERT INTO tasks
                       (id, plan_id, item_id, subtask_id, title, description,
                        target_files, status, priority, created_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (
                        task_id,
                        plan_id,
                        item_id,
                        st.get("id", "subtask-?"),
                        st.get("title", "Untitled subtask"),
                        st.get("description", ""),
                        json.dumps(st.get("target_files", [])),
                        "pending",
                        priority,
                        now,
                    ),
                )
                task_ids.append(task_id)

        log.info("Enqueued %d tasks for %s (plan %s)", len(task_ids), item_id, plan_id)
        return task_ids

    def claim_next_task(self, engine: str = "claude") -> Optional[Dict]:
        """Claim the highest-priority pending task. Returns task dict or None."""
        with self._conn:
            row = self._conn.execute(
                """SELECT id, plan_id, item_id, subtask_id, title, description,
                          target_files, priority
                   FROM tasks
                   WHERE status = 'pending'
                   ORDER BY
                     CASE priority
                       WHEN 'urgent' THEN 0 WHEN 'high' THEN 1
                       WHEN 'medium' THEN 2 WHEN 'low'  THEN 3 ELSE 4
                     END,
                     created_at ASC
                   LIMIT 1""",
            ).fetchone()

            if not row:
                return None

            task_id = row[0]
            self._conn.execute(
                "UPDATE tasks SET status='claimed', engine=?, claimed_at=? WHERE id=?",
                (engine, time.time(), task_id),
            )

        return {
            "id":           row[0],
            "plan_id":      row[1],
            "item_id":      row[2],
            "subtask_id":   row[3],
            "title":        row[4],
            "description":  row[5],
            "target_files": json.loads(row[6] or "[]"),
            "priority":     row[7],
            "engine":       engine,
        }

    def complete_task(
        self,
        task_id: str,
        success: bool,
        result: Optional[Dict] = None,
        error: Optional[str] = None,
    ) -> bool:
        """Mark a claimed task as done or failed. Returns True if row was updated."""
        status = "done" if success else "failed"
        with self._conn:
            cur = self._conn.execute(
                """UPDATE tasks
                   SET status=?, completed_at=?, error=?, result=?
                   WHERE id=? AND status='claimed'""",
                (
                    status,
                    time.time(),
                    error,
                    json.dumps(result) if result else None,
                    task_id,
                ),
            )
        updated = cur.rowcount > 0
        if not updated:
            log.warning("complete_task: task %s not found or not in claimed state", task_id)
        return updated

    def release_task(self, task_id: str) -> bool:
        """Release a claimed task back to pending (e.g. on engine crash)."""
        with self._conn:
            cur = self._conn.execute(
                "UPDATE tasks SET status='pending', engine=NULL, claimed_at=NULL WHERE id=? AND status='claimed'",
                (task_id,),
            )
        return cur.rowcount > 0

    # ── Read operations ──────────────────────────────────────────────────────

    def get_queue_status(self) -> Dict:
        """Return counts by status plus recent task list."""
        rows = self._conn.execute(
            "SELECT status, COUNT(*) FROM tasks GROUP BY status"
        ).fetchall()
        counts: Dict[str, int] = {r[0]: r[1] for r in rows}

        recent = self._conn.execute(
            """SELECT id, item_id, subtask_id, title, status, priority,
                      engine, created_at, completed_at, error
               FROM tasks
               ORDER BY created_at DESC
               LIMIT 20"""
        ).fetchall()

        tasks = [
            {
                "id":           r[0],
                "item_id":      r[1],
                "subtask_id":   r[2],
                "title":        r[3],
                "status":       r[4],
                "priority":     r[5],
                "engine":       r[6],
                "created_at":   r[7],
                "completed_at": r[8],
                "error":        r[9],
            }
            for r in recent
        ]

        return {
            "pending":   counts.get("pending", 0),
            "claimed":   counts.get("claimed", 0),
            "done":      counts.get("done", 0),
            "failed":    counts.get("failed", 0),
            "total":     sum(counts.values()),
            "tasks":     tasks,
        }

    def get_task(self, task_id: str) -> Optional[Dict]:
        row = self._conn.execute(
            """SELECT id, plan_id, item_id, subtask_id, title, description,
                      target_files, status, priority, engine,
                      created_at, claimed_at, completed_at, error, result
               FROM tasks WHERE id=?""",
            (task_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "id":           row[0], "plan_id":      row[1],
            "item_id":      row[2], "subtask_id":   row[3],
            "title":        row[4], "description":  row[5],
            "target_files": json.loads(row[6] or "[]"),
            "status":       row[7], "priority":     row[8],
            "engine":       row[9], "created_at":   row[10],
            "claimed_at":   row[11], "completed_at": row[12],
            "error":        row[13],
            "result":       json.loads(row[14]) if row[14] else None,
        }

    def close(self) -> None:
        self._conn.close()


# ── Module-level singleton ────────────────────────────────────────────────────

_queue: Optional[ExecutionQueue] = None


def get_queue() -> ExecutionQueue:
    global _queue
    if _queue is None:
        _queue = ExecutionQueue()
    return _queue


# ── CLI convenience ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    q = ExecutionQueue()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

    if cmd == "status":
        print(json.dumps(q.get_queue_status(), indent=2))
    elif cmd == "claim":
        engine = sys.argv[2] if len(sys.argv) > 2 else "claude"
        task = q.claim_next_task(engine)
        print(json.dumps(task, indent=2) if task else "No pending tasks")
    elif cmd == "test-enqueue":
        plan = {
            "item_id":  "RM-TEST-001",
            "priority": "high",
            "subtasks": [
                {"id": "s1", "title": "Write tests",  "description": "Add pytest tests", "target_files": ["tests/test_x.py"]},
                {"id": "s2", "title": "Implement API", "description": "Add endpoint",     "target_files": ["framework/api.py"]},
            ],
        }
        ids = q.enqueue_plan(plan)
        print("Enqueued:", ids)
        print(json.dumps(q.get_queue_status(), indent=2))
    else:
        print(f"Unknown command: {cmd}. Use: status | claim [engine] | test-enqueue")
