"""tests/unit/test_persona_loader.py

Unit tests for bin/persona_loader.py (D-17-121).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure bin/ is importable when running from repo root.
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "bin"))

from persona_loader import (
    _strip_front_matter,
    get_persona_metadata,
    list_personas,
    load_persona,
)

KNOWN_PERSONAS = ["code-review", "deliberate-analysis", "decomposition-planner", "voice-fast"]


class TestStripFrontMatter:
    def test_strips_yaml_front_matter(self) -> None:
        text = "---\nid: test\nversion: 1.0.0\n---\n\n# Body\n\nContent here."
        result = _strip_front_matter(text)
        assert result.startswith("# Body")
        assert "id: test" not in result

    def test_no_front_matter_passthrough(self) -> None:
        text = "# System Role\n\nJust a body."
        assert _strip_front_matter(text) == text

    def test_empty_body_after_front_matter(self) -> None:
        text = "---\nid: x\n---\n"
        assert _strip_front_matter(text) == ""


class TestLoadPersona:
    @pytest.mark.parametrize("persona_id", KNOWN_PERSONAS)
    def test_load_known_persona_returns_non_empty(self, persona_id: str) -> None:
        result = load_persona(persona_id, version="1.0.0")
        assert isinstance(result, str)
        assert len(result) > 50, f"Persona '{persona_id}' body suspiciously short"

    @pytest.mark.parametrize("persona_id", KNOWN_PERSONAS)
    def test_load_latest_resolves(self, persona_id: str) -> None:
        result = load_persona(persona_id, version="latest")
        assert len(result) > 50

    @pytest.mark.parametrize("persona_id", KNOWN_PERSONAS)
    def test_front_matter_not_in_output(self, persona_id: str) -> None:
        result = load_persona(persona_id, version="1.0.0")
        assert "deliverable: D-17-121" not in result
        assert "intended_model:" not in result

    def test_load_nonexistent_persona_raises(self) -> None:
        with pytest.raises(FileNotFoundError, match="not found"):
            load_persona("nonexistent-persona-xyz", version="1.0.0")

    def test_empty_persona_id_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            load_persona("")

    def test_whitespace_persona_id_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            load_persona("   ")

    def test_nonexistent_version_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_persona("voice-fast", version="99.99.99")


class TestListPersonas:
    def test_returns_all_known_personas(self) -> None:
        result = list_personas(version="1.0.0")
        for pid in KNOWN_PERSONAS:
            assert pid in result, f"Expected '{pid}' in list_personas() result"

    def test_index_excluded(self) -> None:
        result = list_personas(version="1.0.0")
        assert "INDEX" not in result

    def test_returns_sorted(self) -> None:
        result = list_personas(version="1.0.0")
        assert result == sorted(result)

    def test_latest_resolves(self) -> None:
        result = list_personas(version="latest")
        assert len(result) >= 4


class TestGetPersonaMetadata:
    def test_returns_expected_fields(self) -> None:
        meta = get_persona_metadata("voice-fast", version="1.0.0")
        assert meta.get("id") == "voice-fast"
        assert meta.get("version") == "1.0.0"
        assert meta.get("deliverable") == "D-17-121"

    @pytest.mark.parametrize("persona_id", KNOWN_PERSONAS)
    def test_all_personas_have_deliverable_field(self, persona_id: str) -> None:
        meta = get_persona_metadata(persona_id, version="1.0.0")
        assert meta.get("deliverable") == "D-17-121"

    @pytest.mark.parametrize("persona_id", KNOWN_PERSONAS)
    def test_all_personas_have_intended_model(self, persona_id: str) -> None:
        meta = get_persona_metadata(persona_id, version="1.0.0")
        assert "intended_model" in meta
        assert meta["intended_model"].strip() != ""

    def test_nonexistent_persona_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            get_persona_metadata("does-not-exist", version="1.0.0")
