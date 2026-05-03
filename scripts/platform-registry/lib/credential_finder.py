"""Credential file discovery — METADATA ONLY.

Per Service Registry MVP spec §4.4 and Finding ZZ:
  - Never read or emit credential VALUES.
  - Capture path, size, mtime, mode, and a SHA256 prefix for fingerprint.
  - Map files to services via filename + canonical mount paths.
  - Flag canonical vs stale (suffixed with -PRE-*-INVALID-*, .bak, etc).

The fingerprint is the first 12 hex chars of SHA256(file). It lets us
detect drift between two paths claiming to be the same secret without
ever revealing what the secret is. Two files with the same fingerprint
hold the same bytes; same prefix collisions are statistically negligible
at this scale.
"""

from __future__ import annotations

import hashlib
import os
import re
import stat
from dataclasses import dataclass, field
from pathlib import Path

HOME = Path.home()

VAULT_AGENT_ROOT = HOME / ".vault-agent-secrets"
SEARCH_ROOTS = (
    HOME,  # depth-limited; for vault-init-keys-* and friends
    HOME / "control-center-stack",
    Path("/Users/admin/repos/integrated-ai-platform/docker"),
)

# Filename patterns we consider credential-bearing
CREDENTIAL_GLOBS = (
    "vault-init-keys*",
    ".vault-token",
    "credentials.env",
    "role-id",
    "secret-id",
    ".env",
    ".env.local",
    ".env.production",
)

# Stale markers (case-insensitive substring match in basename)
STALE_MARKERS = (
    "INVALID",
    "PRE-",
    ".bak",
    ".old",
    ".retired",
    ".PRE-KV-LOSS",
)

# Files that are EXAMPLE templates, not real credentials
EXAMPLE_MARKERS = (".example", ".sample", ".template")

MAX_TOP_DEPTH = 1  # search HOME at depth=1 (don't recurse into ~/Library etc.)


@dataclass
class CredentialFile:
    path: str
    basename: str
    size: int
    mtime_iso: str
    mode_octal: str  # "0600", "0644" etc.
    fingerprint: str  # first 12 hex chars of SHA256
    classification: str  # "canonical" | "stale" | "example" | "unknown"
    service_hint: str | None = None  # service_id this likely belongs to
    notes: list[str] = field(default_factory=list)


def _sha256_prefix(path: Path, n: int = 12) -> str:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()[:n]
    except OSError:
        return "unreadable"


def _classify(path: Path) -> str:
    name_lower = path.name.lower()
    if any(m in path.name for m in EXAMPLE_MARKERS):
        return "example"
    if any(m.lower() in name_lower for m in STALE_MARKERS):
        return "stale"
    if any(m in path.name for m in STALE_MARKERS):  # case-sensitive PRE- etc.
        return "stale"
    return "canonical"


def _service_hint(path: Path) -> str | None:
    """Best-effort service mapping. Vault Agent layout has the canonical
    structure ~/.vault-agent-secrets/<service>/..."""
    try:
        rel = path.relative_to(VAULT_AGENT_ROOT)
        return rel.parts[0] if rel.parts else None
    except ValueError:
        pass
    # docker/<stack>/.env → stack hint
    try:
        rel = path.relative_to(Path("/Users/admin/repos/integrated-ai-platform/docker"))
        return rel.parts[0] if len(rel.parts) > 1 else None
    except ValueError:
        pass
    return None


def _file_metadata(path: Path) -> CredentialFile | None:
    try:
        st = path.stat()
    except OSError:
        return None
    if not stat.S_ISREG(st.st_mode):
        return None
    classification = _classify(path)
    return CredentialFile(
        path=str(path),
        basename=path.name,
        size=st.st_size,
        mtime_iso=_iso(st.st_mtime),
        mode_octal=oct(st.st_mode & 0o777).replace("0o", "0"),
        fingerprint=_sha256_prefix(path),
        classification=classification,
        service_hint=_service_hint(path),
    )


def _iso(epoch: float) -> str:
    import datetime as dt

    return dt.datetime.fromtimestamp(epoch).isoformat(timespec="seconds")


def _iter_home_top_level() -> list[Path]:
    """Top-level files in HOME matching credential globs (depth-1 only)."""
    out: list[Path] = []
    if not HOME.exists():
        return out
    for p in HOME.iterdir():
        if not p.is_file():
            continue
        for pattern in CREDENTIAL_GLOBS:
            if p.match(pattern):
                out.append(p)
                break
    return out


def _iter_vault_agent_secrets() -> list[Path]:
    out: list[Path] = []
    if not VAULT_AGENT_ROOT.exists():
        return out
    for p in VAULT_AGENT_ROOT.rglob("*"):
        if not p.is_file():
            continue
        for pattern in CREDENTIAL_GLOBS:
            if p.match(pattern):
                out.append(p)
                break
    return out


def _iter_compose_envs() -> list[Path]:
    """`.env` (not .env.example) under docker/ trees we own."""
    out: list[Path] = []
    for root in (
        Path("/Users/admin/repos/integrated-ai-platform/docker"),
        HOME / "control-center-stack",
    ):
        if not root.exists():
            continue
        for p in root.rglob(".env*"):
            if not p.is_file():
                continue
            out.append(p)
    return out


def find_all() -> list[CredentialFile]:
    """Discover every credential-bearing file we know how to look for."""
    paths: list[Path] = []
    paths.extend(_iter_home_top_level())
    paths.extend(_iter_vault_agent_secrets())
    paths.extend(_iter_compose_envs())
    # de-dupe by resolved path
    seen: set[str] = set()
    out: list[CredentialFile] = []
    for p in paths:
        try:
            real = str(p.resolve())
        except OSError:
            real = str(p)
        if real in seen:
            continue
        seen.add(real)
        meta = _file_metadata(p)
        if meta is not None:
            out.append(meta)
    return out


def attach_to_merged(
    merged: list[dict],
    creds: list[CredentialFile],
    runtime_orphans: list[dict] | None = None,
) -> list[dict]:
    """Attach credential metadata into merged service records' `credentials`
    field. Only canonical files are attached; stale + example files are
    enumerated separately at the top-level registry, not per-service."""
    by_id: dict[str, dict] = {}
    for r in list(merged) + list(runtime_orphans or []):
        by_id[r["service_id"]] = r
        by_id.setdefault(r["container_name"], r)

    for c in creds:
        if c.classification != "canonical":
            continue
        if not c.service_hint:
            continue
        target = by_id.get(c.service_hint)
        if target is None:
            continue
        target.setdefault("credentials", {})
        target["credentials"].setdefault("files", []).append(
            {
                "path": c.path,
                "basename": c.basename,
                "size": c.size,
                "mode": c.mode_octal,
                "mtime": c.mtime_iso,
                "fingerprint": c.fingerprint,
                "classification": c.classification,
            }
        )
    return merged


def summarize(creds: list[CredentialFile]) -> dict:
    """Top-level summary suitable for inventory.json metadata block."""
    by_class: dict[str, int] = {}
    for c in creds:
        by_class[c.classification] = by_class.get(c.classification, 0) + 1
    # find duplicate fingerprints — same secret bytes in two locations
    fp_paths: dict[str, list[str]] = {}
    for c in creds:
        if c.classification != "canonical" or c.fingerprint == "unreadable":
            continue
        fp_paths.setdefault(c.fingerprint, []).append(c.path)
    duplicates = {fp: paths for fp, paths in fp_paths.items() if len(paths) > 1}
    return {
        "total": len(creds),
        "by_classification": by_class,
        "duplicate_fingerprints": duplicates,
    }


if __name__ == "__main__":
    creds = find_all()
    summary = summarize(creds)
    print(f"credential files: {summary['total']}")
    print(f"  by classification: {summary['by_classification']}")
    if summary["duplicate_fingerprints"]:
        print(f"  DUPLICATE fingerprints (same secret bytes in N places):")
        for fp, paths in summary["duplicate_fingerprints"].items():
            print(f"    {fp}: {len(paths)} copies")
            for p in paths:
                print(f"      {p}")
    print(f"\nSample (first 8):")
    for c in creds[:8]:
        print(
            f"  [{c.classification:9s}] {c.basename:30s} "
            f"size={c.size:6d} mode={c.mode_octal} fp={c.fingerprint} "
            f"svc={c.service_hint}"
        )
