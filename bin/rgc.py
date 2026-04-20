#!/usr/bin/env python3
"""rgc — Roadmap Governance Core CLI.

Usage:
    python3 bin/rgc.py roadmap sync [--dry-run] [--db-url URL]
    python3 bin/rgc.py integrity run [--dry-run] [--db-url URL] [--artifact-dir DIR]
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


@click.group()
def cli() -> None:
    """Roadmap Governance Core (RGC) command-line interface."""


@cli.group()
def roadmap() -> None:
    """Roadmap item commands."""


@roadmap.command("sync")
@click.option(
    "--db-url",
    envvar="RGC_DATABASE_URL",
    default=None,
    help="Database URL (default: sqlite:///rgc.db or $RGC_DATABASE_URL).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Parse and validate without writing to the database.",
)
def sync_cmd(db_url: str | None, dry_run: bool) -> None:
    """Sync roadmap items from docs/roadmap/ROADMAP_INDEX.md into the database."""
    import os

    if db_url:
        os.environ["RGC_DATABASE_URL"] = db_url

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from roadmap_governance.database import get_db_url
    from roadmap_governance.models import Base
    from roadmap_governance.service import sync_roadmap

    url = get_db_url()
    kwargs: dict = {}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}

    engine = create_engine(url, **kwargs)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    db = factory()

    try:
        result = sync_roadmap(db, REPO_ROOT, dry_run=dry_run)
    finally:
        db.close()

    mode = "DRY RUN — " if dry_run else ""
    click.echo(f"{mode}Sync complete.")
    click.echo(f"  items created:   {result.items_created}")
    click.echo(f"  items updated:   {result.items_updated}")
    click.echo(f"  items unchanged: {result.items_unchanged}")
    click.echo(f"  findings created: {result.findings_created}")


@cli.group()
def integrity() -> None:
    """Integrity review commands."""


@integrity.command("run")
@click.option(
    "--db-url",
    envvar="RGC_DATABASE_URL",
    default=None,
    help="Database URL (default: sqlite:///rgc.db or $RGC_DATABASE_URL).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Check without writing findings or artifacts.",
)
@click.option(
    "--artifact-dir",
    default=None,
    help="Override artifact output directory.",
)
def integrity_run_cmd(db_url: str | None, dry_run: bool, artifact_dir: str | None) -> None:
    """Run integrity review against current roadmap items in the database."""
    import os

    if db_url:
        os.environ["RGC_DATABASE_URL"] = db_url

    from pathlib import Path as _Path

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from roadmap_governance.database import get_db_url
    from roadmap_governance.integrity import run_integrity_review
    from roadmap_governance.models import Base

    url = get_db_url()
    kwargs: dict = {}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}

    engine = create_engine(url, **kwargs)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    db = factory()

    art_dir = _Path(artifact_dir) if artifact_dir else None

    try:
        result = run_integrity_review(db, REPO_ROOT, artifact_dir=art_dir, dry_run=dry_run)
    finally:
        db.close()

    mode = "DRY RUN — " if dry_run else ""
    click.echo(f"{mode}Integrity review complete.")
    click.echo(f"  items checked:     {result.items_checked}")
    click.echo(f"  findings created:  {result.findings_created}")
    click.echo(f"  findings skipped:  {result.findings_skipped}")
    if result.artifact_path:
        click.echo(f"  artifact:          {result.artifact_path}")
    if result.check_counts:
        for check, count in sorted(result.check_counts.items()):
            click.echo(f"    {check}: {count}")


if __name__ == "__main__":
    cli()
