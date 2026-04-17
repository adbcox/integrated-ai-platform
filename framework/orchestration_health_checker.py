from typing import Any


def check_orchestration_health(
    layer_results: list[dict[str, Any]], layer_names: list[str]
) -> dict[str, Any]:
    if (
        not isinstance(layer_results, list)
        or not isinstance(layer_names, list)
        or len(layer_results) != len(layer_names)
    ):
        return {
            "health_valid": False,
            "layer_count": 0,
            "healthy_count": 0,
            "unhealthy_count": 0,
            "unhealthy_layers": [],
            "health_score": 0.0,
            "health_status": "invalid_input",
        }

    healthy_count = 0
    unhealthy_layers = []

    for index, result in enumerate(layer_results):
        layer_name = layer_names[index]
        valid_key = ""
        valid_value = False

        if isinstance(result, dict):
            for key in result.keys():
                if key.endswith("_valid"):
                    valid_key = key
                    valid_value = result.get(key) is True
                    break

        if valid_key and valid_value:
            healthy_count += 1
        else:
            unhealthy_layers.append(layer_name)

    layer_count = len(layer_names)
    unhealthy_count = len(unhealthy_layers)
    health_score = (
        round((healthy_count / float(layer_count)) * 100.0, 3)
        if layer_count > 0
        else 0.0
    )

    if health_score == 100.0:
        status = "healthy"
    elif health_score >= 50.0:
        status = "degraded"
    else:
        status = "critical"

    return {
        "health_valid": True,
        "layer_count": layer_count,
        "healthy_count": healthy_count,
        "unhealthy_count": unhealthy_count,
        "unhealthy_layers": unhealthy_layers,
        "health_score": health_score,
        "health_status": status,
    }


def summarize_health_check(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("health_valid") is not True:
        return {
            "summary_valid": False,
            "health_status": "invalid_input",
            "health_score": 0.0,
            "unhealthy_count": 0,
        }

    return {
        "summary_valid": True,
        "health_status": result.get("health_status", "invalid_input"),
        "health_score": float(result.get("health_score", 0.0)),
        "unhealthy_count": int(result.get("unhealthy_count", 0)),
    }
