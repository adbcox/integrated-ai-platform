"""Standalone FastAPI application for the RGC subsystem.

Run:
    RGC_DATABASE_URL=sqlite:///rgc.db uvicorn roadmap_governance.api_app:app
    PORT=8020 uvicorn roadmap_governance.api_app:app --host 0.0.0.0 --port $PORT

The app auto-creates tables on startup (SQLite local-first); for PostgreSQL use
Alembic migrations: `alembic upgrade head`.
"""

from __future__ import annotations

from fastapi import FastAPI

from roadmap_governance.database import _get_engine
from roadmap_governance.models import Base
from roadmap_governance.router import router

app = FastAPI(
    title="Roadmap Governance Core",
    description="RGC read-only API: roadmap items and integrity findings.",
    version="0.1.0",
)

app.include_router(router)


@app.on_event("startup")
def _create_tables() -> None:
    """Ensure tables exist (safe for SQLite local-first; skipped if already present)."""
    Base.metadata.create_all(_get_engine())
