import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "bin/validate_next_tier_autonomy_expansion.py"
ARTIFACT = REPO_ROOT / "artifacts/validation/next_tier_autonomy_expansion_validation.json"


def test_next_tier_autonomy_expansion_validator_passes() -> None:
    result = subprocess.run(
        ["python3", str(VALIDATOR)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert payload["status"] == "PASS"
    assert set(payload["connector_policy_connectors"]) == {
        "github",
        "gmail",
        "google_calendar",
    }
    assert payload["checked_items"] == ["RM-GOV-009", "RM-AUTO-001", "RM-DEV-001"]
