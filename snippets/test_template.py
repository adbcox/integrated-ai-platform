"""Pytest patterns for bounded task tests."""

from __future__ import annotations

import pytest


def test_happy_path() -> None:
    """Template happy-path assertion."""
    assert True


@pytest.mark.parametrize("value", [1, 2, 3])
def test_parametrized(value: int) -> None:
    """Template parameterized test."""
    assert value > 0
