"""Offline regression for framework.model_profiles."""

from __future__ import annotations

import unittest

from framework.model_profiles import (
    DEFAULT_BACKEND,
    ModelProfile,
    get_profile,
    list_active_profiles,
    list_profile_names,
    resolve_profile_for_task_class,
)


class ModelProfilesTest(unittest.TestCase):
    def test_at_least_three_active_profiles_exist(self) -> None:
        active = list_active_profiles()
        self.assertGreaterEqual(len(active), 3)
        names = {p.profile_name for p in active}
        self.assertTrue({"fast", "balanced", "hard"}.issubset(names))

    def test_active_profiles_use_default_backend(self) -> None:
        for profile in list_active_profiles():
            self.assertEqual(profile.backend, DEFAULT_BACKEND)

    def test_profiles_expose_required_fields(self) -> None:
        for profile in list_active_profiles():
            self.assertIsInstance(profile, ModelProfile)
            self.assertTrue(profile.profile_name)
            self.assertTrue(profile.model)
            self.assertGreater(profile.context_window, 0)
            self.assertGreater(profile.timeout_seconds, 0)
            self.assertGreaterEqual(profile.retry_budget, 0)
            self.assertGreaterEqual(profile.temperature, 0.0)
            self.assertIsInstance(profile.intended_task_classes, tuple)

    def test_get_profile_lookup(self) -> None:
        fast = get_profile("fast")
        self.assertEqual(fast.profile_name, "fast")
        with self.assertRaises(KeyError):
            get_profile("nonexistent")

    def test_resolve_profile_for_task_class(self) -> None:
        self.assertEqual(
            resolve_profile_for_task_class("quick_fix").profile_name, "fast"
        )
        self.assertEqual(
            resolve_profile_for_task_class("multi_file_edit").profile_name, "balanced"
        )
        self.assertEqual(
            resolve_profile_for_task_class("hard_debug").profile_name, "hard"
        )
        self.assertEqual(
            resolve_profile_for_task_class("unknown_class").profile_name, "balanced"
        )

    def test_profile_name_list_deterministic(self) -> None:
        self.assertEqual(list_profile_names(), sorted(list_profile_names()))

    def test_profile_to_dict_roundtrips(self) -> None:
        d = get_profile("balanced").to_dict()
        self.assertEqual(d["profile_name"], "balanced")
        self.assertEqual(d["backend"], DEFAULT_BACKEND)
        self.assertIsInstance(d["intended_task_classes"], list)


if __name__ == "__main__":
    unittest.main()
