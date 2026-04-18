from typing import Any

def config_layer_aggregator(input_dict):
    if not isinstance(input_dict, dict):
        return {"config_layer_status": "invalid"}
    return {"config_layer_status": "aggregated"}
