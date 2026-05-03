"""Artifact axis writer — emits ~/.platform-registry/artifacts.json + per-deliverable slices.

Sibling to registry_writer.py (D-17-29 service axis); D-17-37 substrate.

Walks the QNAP roadmap-artifacts tree and emits structured records
keyed by deliverable-id. Per spec: source/, extracted/, annotations/,
metadata.yaml under each deliverable.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

DEFAULT_OUTPUT = Path.home() / ".platform-registry"
DEFAULT_ROOT = Path("/Users/admin/mnt/qnap-downloads/manual/roadmap-artifacts")
QNAP_URI_PREFIX = "qnap://download/manual/roadmap-artifacts"

ACL_CLASSES = ("property", "schematics", "vendor-docs", "source-files")


def _sha256_head(path: Path, max_bytes: int = 1_048_576) -> str:
    """First-MiB sha256 — fast fingerprint, not full integrity."""
    h = hashlib.sha256()
    try:
        with path.open("rb") as f:
            h.update(f.read(max_bytes))
    except OSError:
        return ""
    return h.hexdigest()[:16]


def _file_record(p: Path, root: Path) -> dict[str, Any]:
    st = p.stat()
    return {
        "path_local": str(p),
        "path_qnap_uri": _to_qnap_uri(p),
        "basename": p.name,
        "size_bytes": st.st_size,
        "mode": oct(st.st_mode & 0o777),
        "mtime": dt.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
        "sha256_head_1mib": _sha256_head(p),
    }


def _to_qnap_uri(p: Path) -> str:
    """Convert /Users/admin/mnt/qnap-downloads/manual/roadmap-artifacts/<rest>
    to qnap://download/manual/roadmap-artifacts/<rest>."""
    try:
        rel = p.relative_to(DEFAULT_ROOT)
    except ValueError:
        return ""
    return f"{QNAP_URI_PREFIX}/{rel}"


def _read_metadata(deliverable_dir: Path) -> dict[str, Any]:
    meta = deliverable_dir / "metadata.yaml"
    if not meta.exists():
        return {}
    # Lightweight parse — full yaml dep optional. Just record presence + size.
    return {
        "present": True,
        "path_local": str(meta),
        "path_qnap_uri": _to_qnap_uri(meta),
        "size_bytes": meta.stat().st_size,
    }


def scan_deliverable(deliverable_dir: Path, root: Path) -> dict[str, Any]:
    """Build one deliverable record. Walks source/ extracted/ annotations/."""
    deliverable_id = deliverable_dir.name
    record: dict[str, Any] = {
        "deliverable_id": deliverable_id,
        "phase": deliverable_dir.parent.name,
        "qnap_dir_uri": _to_qnap_uri(deliverable_dir),
        "local_dir": str(deliverable_dir),
        "metadata": _read_metadata(deliverable_dir),
        "files": {"source": [], "extracted": [], "annotations": []},
        "acl_class": None,
        "acl_class_source": "metadata-or-default",
    }
    for subname in ("source", "extracted", "annotations"):
        sub = deliverable_dir / subname
        if not sub.is_dir():
            continue
        for f in sorted(sub.rglob("*")):
            if f.is_file() and not f.name.startswith("."):
                record["files"][subname].append(_file_record(f, root))
    # ACL class inference: read first non-empty line of metadata.yaml
    meta = deliverable_dir / "metadata.yaml"
    if meta.exists():
        try:
            for line in meta.read_text().splitlines():
                line = line.strip()
                if line.startswith("acl_class:"):
                    val = line.split(":", 1)[1].strip().strip("'\"")
                    if val in ACL_CLASSES:
                        record["acl_class"] = val
                        record["acl_class_source"] = "metadata.yaml"
                    break
        except OSError:
            pass
    return record


def build_artifacts(root: Path = DEFAULT_ROOT) -> tuple[list[dict], dict]:
    """Walk the QNAP tree. Return (records, metadata)."""
    t0 = dt.datetime.now()
    errors: list[str] = []
    records: list[dict] = []

    if not root.exists():
        errors.append(f"root missing: {root}")
        return records, _meta(t0, records, root, errors, mounted=False)

    if not os.access(root, os.R_OK):
        errors.append(f"root unreadable: {root}")
        return records, _meta(t0, records, root, errors, mounted=False)

    for phase_dir in sorted(root.iterdir()):
        if not phase_dir.is_dir() or phase_dir.name.startswith("."):
            continue
        for deliverable_dir in sorted(phase_dir.iterdir()):
            if not deliverable_dir.is_dir() or deliverable_dir.name.startswith("."):
                continue
            try:
                records.append(scan_deliverable(deliverable_dir, root))
            except OSError as e:
                errors.append(f"scan failed {deliverable_dir}: {e}")
    return records, _meta(t0, records, root, errors, mounted=True)


def _meta(t0: dt.datetime, records: list[dict], root: Path, errors: list[str], mounted: bool) -> dict:
    return {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "elapsed_seconds": round((dt.datetime.now() - t0).total_seconds(), 3),
        "root": str(root),
        "qnap_mounted": mounted,
        "counts": {
            "deliverables": len(records),
            "files": sum(
                len(r["files"]["source"])
                + len(r["files"]["extracted"])
                + len(r["files"]["annotations"])
                for r in records
            ),
        },
        "errors": errors,
    }


def write_artifacts(records: list[dict], metadata: dict, output_dir: Path = DEFAULT_OUTPUT) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir = output_dir / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)

    index_path = output_dir / "artifacts.json"
    refresh_path = output_dir / "artifacts-last-refresh.json"

    full = {"schema_version": "1.0", "deliverables": records, "metadata": metadata}
    index_path.write_text(json.dumps(full, indent=2, default=str))
    refresh_path.write_text(json.dumps(metadata, indent=2, default=str))

    for old in artifacts_dir.glob("*.json"):
        old.unlink()
    paths: dict[str, Path] = {"artifacts-index": index_path, "artifacts-last-refresh": refresh_path}
    for r in records:
        sid = _safe_filename(r["deliverable_id"])
        p = artifacts_dir / f"{sid}.json"
        p.write_text(json.dumps(r, indent=2, default=str))
        paths[r["deliverable_id"]] = p
    return paths


def _safe_filename(s: str) -> str:
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in s)


def query(deliverable_id: str, output_dir: Path = DEFAULT_OUTPUT) -> dict | None:
    p = output_dir / "artifacts" / f"{_safe_filename(deliverable_id)}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text())


def refresh(output_dir: Path = DEFAULT_OUTPUT, root: Path = DEFAULT_ROOT) -> dict:
    records, metadata = build_artifacts(root)
    write_artifacts(records, metadata, output_dir)
    return metadata


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT
    meta = refresh(out)
    print(json.dumps(meta, indent=2, default=str))
