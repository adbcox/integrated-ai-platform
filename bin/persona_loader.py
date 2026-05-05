#!/usr/bin/env python3
"""
persona_loader.py — Load system prompt personas from the versioned library (D-17-121).

Library root: config/prompts/library/
Persona files: v<version>/personas/<id>.md

Usage:
    from bin.persona_loader import load_persona
    system_prompt = load_persona("code-review")
    system_prompt = load_persona("voice-fast", version="1.0.0")
"""

from __future__ import annotations

import re
from pathlib import Path

LIBRARY_ROOT = Path(__file__).parent.parent / "config" / "prompts" / "library"

_FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def _resolve_version(version: str) -> str:
    """Resolve 'latest' to the highest semver string (without 'v' prefix) that has a personas/ dir."""
    if version != "latest":
        return version.lstrip("v")
    candidates = [
        d.name[1:]  # strip leading 'v' → bare semver
        for d in LIBRARY_ROOT.iterdir()
        if d.is_dir()
        and re.match(r"^v\d+\.\d+\.\d+$", d.name)
        and (d / "personas").is_dir()
    ]
    if not candidates:
        raise FileNotFoundError(
            f"No versioned directories with personas/ found under {LIBRARY_ROOT}"
        )
    return sorted(candidates, key=lambda s: tuple(int(x) for x in s.split(".")))[-1]


def _strip_front_matter(text: str) -> str:
    """Remove YAML front-matter block if present; return body only."""
    match = _FRONT_MATTER_RE.match(text)
    if match:
        return text[match.end():].lstrip("\n")
    return text


def load_persona(persona_id: str, version: str = "latest") -> str:
    """Return the system prompt body for the given persona id and version.

    Args:
        persona_id: One of 'voice-fast', 'deliberate-analysis', 'code-review',
                    'decomposition-planner', or any future persona id.
        version: Semver string like '1.0.0', or 'latest' (default) to auto-resolve.

    Returns:
        System prompt string with front-matter stripped.

    Raises:
        FileNotFoundError: Persona file or version directory does not exist.
        ValueError: persona_id is empty.
    """
    if not persona_id or not persona_id.strip():
        raise ValueError("persona_id must be a non-empty string")

    resolved = _resolve_version(version)
    persona_path = LIBRARY_ROOT / f"v{resolved}" / "personas" / f"{persona_id}.md"

    if not persona_path.exists():
        available = _list_personas(resolved)
        raise FileNotFoundError(
            f"Persona '{persona_id}' not found in library version {resolved}. "
            f"Available: {available}"
        )

    raw = persona_path.read_text(encoding="utf-8")
    return _strip_front_matter(raw)


def list_personas(version: str = "latest") -> list[str]:
    """Return sorted list of available persona ids for the given version."""
    resolved = _resolve_version(version)
    return _list_personas(resolved)


def _list_personas(resolved_version: str) -> list[str]:
    personas_dir = LIBRARY_ROOT / f"v{resolved_version}" / "personas"
    if not personas_dir.exists():
        return []
    return sorted(
        p.stem for p in personas_dir.glob("*.md")
        if p.stem != "INDEX"
    )


def get_persona_metadata(persona_id: str, version: str = "latest") -> dict[str, str]:
    """Return the front-matter fields as a dict for the given persona."""
    resolved = _resolve_version(version)
    persona_path = LIBRARY_ROOT / f"v{resolved}" / "personas" / f"{persona_id}.md"

    if not persona_path.exists():
        raise FileNotFoundError(f"Persona '{persona_id}' not found in version {resolved}")

    raw = persona_path.read_text(encoding="utf-8")
    match = _FRONT_MATTER_RE.match(raw)
    if not match:
        return {}

    metadata: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            metadata[key.strip()] = value.strip()
    return metadata


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: persona_loader.py <persona_id> [version]", file=sys.stderr)
        sys.exit(1)

    pid = sys.argv[1]
    ver = sys.argv[2] if len(sys.argv) > 2 else "latest"
    print(load_persona(pid, ver))
