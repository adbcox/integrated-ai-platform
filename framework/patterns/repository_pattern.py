"""Repository pattern — abstract persistence behind a clean interface.

Use when: decoupling business logic from storage details (JSON files, SQLite,
         APIs). Makes testing easy (swap real repo for in-memory fake).
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
import json
from typing import Optional


@dataclass
class Record:
    id: str
    data: dict = field(default_factory=dict)


class Repository(ABC):
    @abstractmethod
    def get(self, id: str) -> Optional[Record]: ...

    @abstractmethod
    def save(self, record: Record) -> None: ...

    @abstractmethod
    def delete(self, id: str) -> None: ...

    @abstractmethod
    def list_all(self) -> list[Record]: ...


class JsonFileRepository(Repository):
    def __init__(self, path: Path) -> None:
        self.path = path
        self._store: dict[str, dict] = {}
        if path.exists():
            self._store = json.loads(path.read_text())

    def _flush(self) -> None:
        self.path.write_text(json.dumps(self._store, indent=2))

    def get(self, id: str) -> Optional[Record]:
        raw = self._store.get(id)
        return Record(id=id, data=raw) if raw is not None else None

    def save(self, record: Record) -> None:
        self._store[record.id] = record.data
        self._flush()

    def delete(self, id: str) -> None:
        self._store.pop(id, None)
        self._flush()

    def list_all(self) -> list[Record]:
        return [Record(id=k, data=v) for k, v in self._store.items()]


class InMemoryRepository(Repository):
    """Use this in tests — no disk I/O."""
    def __init__(self) -> None:
        self._store: dict[str, Record] = {}

    def get(self, id: str) -> Optional[Record]:
        return self._store.get(id)

    def save(self, record: Record) -> None:
        self._store[record.id] = record

    def delete(self, id: str) -> None:
        self._store.pop(id, None)

    def list_all(self) -> list[Record]:
        return list(self._store.values())
