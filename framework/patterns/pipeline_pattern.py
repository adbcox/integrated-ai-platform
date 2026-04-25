"""Pipeline pattern — chain of processing steps, each transforming data.

Use when: data flows through sequential transformations (ETL, RAG stages,
         media processing, document ingestion, inference chains).
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass
class Context:
    data: Any
    metadata: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


class Stage(ABC):
    @abstractmethod
    def process(self, ctx: Context) -> Context: ...

    def __call__(self, ctx: Context) -> Context:
        if not ctx.ok:
            return ctx  # short-circuit on error
        return self.process(ctx)


class Pipeline:
    def __init__(self, *stages: Stage) -> None:
        self.stages = list(stages)

    def add(self, stage: Stage) -> "Pipeline":
        self.stages.append(stage)
        return self

    def run(self, data: Any) -> Context:
        ctx = Context(data=data)
        for stage in self.stages:
            ctx = stage(ctx)
        return ctx


# ── Concrete example ────────────────────────────────────────────────────────

class Validate(Stage):
    def process(self, ctx: Context) -> Context:
        if not ctx.data:
            ctx.errors.append("empty input")
        return ctx


class Normalize(Stage):
    def process(self, ctx: Context) -> Context:
        if isinstance(ctx.data, str):
            ctx.data = ctx.data.strip().lower()
        return ctx


class Enrich(Stage):
    def process(self, ctx: Context) -> Context:
        ctx.metadata["length"] = len(str(ctx.data))
        return ctx


if __name__ == "__main__":
    pipeline = Pipeline(Validate(), Normalize(), Enrich())
    result = pipeline.run("  Hello World  ")
    print(result.data, result.metadata)  # "hello world" {'length': 11}
