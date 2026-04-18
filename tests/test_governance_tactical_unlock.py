"""Offline coverage for RECON-W2 tactical unlock criteria."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GOV_DIR = REPO_ROOT / "governance"


def _load(name: str) -> dict:
    return json.loads((GOV_DIR / name).read_text(encoding="utf-8"))


def _live_framework_prefixes() -> set[str]:
    files = subprocess.check_output(
        ["git", "ls-files", "framework/"],
        cwd=REPO_ROOT,
        text=True,
    ).splitlines()
    prefixes: set[str] = set()
    for family_prefix in ("eo_", "ed_", "mc_", "multi_phase_", "live_bridge_", "ort_", "pgs_"):
        if any(f.startswith(f"framework/{family_prefix}") for f in files):
            prefixes.add(family_prefix)
    return prefixes


class TacticalUnlockTest(unittest.TestCase):
    def test_every_discoverable_family_prefix_is_represented(self) -> None:
        payload = _load("tactical_unlock_criteria.json")
        represented: set[str] = set()
        for family in payload["families"]:
            for p in family["prefixes"]:
                represented.add(p)
        live = _live_framework_prefixes()
        self.assertTrue(
            live.issubset(represented),
            f"unrepresented family prefixes: {live - represented}",
        )

    def test_every_family_unlock_state_is_locked(self) -> None:
        payload = _load("tactical_unlock_criteria.json")
        for family in payload["families"]:
            self.assertEqual(
                family["unlock_state"],
                "locked",
                f"family {family['family_id']} is not locked",
            )

    def test_live_bridge_references_adr_0003(self) -> None:
        payload = _load("tactical_unlock_criteria.json")
        lob = next(
            (f for f in payload["families"] if f["family_id"] == "live_bridge"),
            None,
        )
        self.assertIsNotNone(lob)
        assert lob is not None
        self.assertEqual(lob["unlock_state"], "locked")
        self.assertIn("adr_ref", lob)
        self.assertIn("0003", lob["adr_ref"])

    def test_review_packet_required_is_true_for_all(self) -> None:
        payload = _load("tactical_unlock_criteria.json")
        for family in payload["families"]:
            self.assertTrue(family["review_packet_required"])


if __name__ == "__main__":
    unittest.main()
