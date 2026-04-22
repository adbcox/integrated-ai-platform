import importlib.util
from pathlib import Path


def _load_module():
    module_path = Path(__file__).resolve().parents[1] / "bin" / "compute_next_pull.py"
    spec = importlib.util.spec_from_file_location("compute_next_pull", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_placeholder_state_conflict_blocks_candidate():
    module = _load_module()
    item = {
        "status": "proposed",
        "execution": {"execution_status": "completed"},
        "validation": {"validation_status": "completed"},
    }
    assert module.placeholder_state_conflict(item) is True


def test_compute_next_pull_filters_archived_and_placeholder():
    module = _load_module()
    items = {
        "RM-READY-001": {
            "id": "RM-READY-001",
            "title": "Ready item",
            "status": "proposed",
            "priority": "P1",
            "category": "GOV",
            "dependencies": {"depends_on": []},
            "execution": {"execution_status": "not_started"},
            "validation": {"validation_status": "not_started"},
            "ai_operability": {
                "allowed_files": ["docs/**"],
                "forbidden_files": ["runtime/**"],
                "validation_order": ["step-1"],
                "rollback_rule": "revert file",
                "artifact_outputs": ["artifacts/example.json"],
            },
            "governance": {
                "phase_target": "Phase 1",
                "architectural_lane": "governed_loop",
            },
            "_source_path": "docs/roadmap/items/RM-READY-001.yaml",
        },
        "RM-ARCH-001": {
            "id": "RM-ARCH-001",
            "title": "Archived item",
            "status": "completed",
            "archive_status": "archived",
            "priority": "P1",
            "category": "GOV",
            "dependencies": {"depends_on": []},
            "execution": {"execution_status": "complete"},
            "validation": {"validation_status": "passed"},
            "ai_operability": {
                "allowed_files": ["docs/**"],
                "forbidden_files": ["runtime/**"],
                "validation_order": ["step-1"],
                "rollback_rule": "revert file",
                "artifact_outputs": ["artifacts/example.json"],
            },
            "governance": {
                "phase_target": "Phase 1",
                "architectural_lane": "governed_loop",
            },
            "_source_path": "docs/roadmap/items/RM-ARCH-001.yaml",
        },
        "RM-PLACEHOLDER-001": {
            "id": "RM-PLACEHOLDER-001",
            "title": "Placeholder drift",
            "status": "proposed",
            "priority": "P1",
            "category": "DEV",
            "dependencies": {"depends_on": []},
            "execution": {"execution_status": "completed"},
            "validation": {"validation_status": "completed"},
            "ai_operability": {
                "allowed_files": ["docs/**"],
                "forbidden_files": ["runtime/**"],
                "validation_order": ["step-1"],
                "rollback_rule": "revert file",
                "artifact_outputs": ["artifacts/example.json"],
            },
            "governance": {
                "phase_target": "Phase 1",
                "architectural_lane": "governed_loop",
            },
            "_source_path": "docs/roadmap/items/RM-PLACEHOLDER-001.yaml",
        },
    }

    plan = module.compute_next_pull(items)
    assert plan["chosen_next_item"] == "RM-READY-001"
    assert "RM-ARCH-001" in plan["archived_items"]
    assert "RM-PLACEHOLDER-001" in plan["blocked_placeholder_items"]
