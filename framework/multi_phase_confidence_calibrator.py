from typing import Any


def calibrate_confidence(
    quality: dict[str, Any],
    training_signal: dict[str, Any],
    calibration_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(quality, dict)
        or not isinstance(training_signal, dict)
        or not isinstance(calibration_config, dict)
    ):
        return {
            "calibration_status": "invalid_input",
            "calibrated_score": 0.0,
            "calibration_phase": None,
        }

    quality_ok = quality.get("quality_status") == "scored"
    signal_ok = training_signal.get("signal_status") == "generated"

    if quality_ok and signal_ok:
        return {
            "calibration_status": "calibrated",
            "calibrated_score": quality.get("quality_score", 0.0),
            "calibration_phase": quality.get("quality_phase"),
        }

    if not signal_ok:
        return {
            "calibration_status": "no_signal",
            "calibrated_score": 0.0,
            "calibration_phase": None,
        }

    return {
        "calibration_status": "invalid_input",
        "calibrated_score": 0.0,
        "calibration_phase": None,
    }
