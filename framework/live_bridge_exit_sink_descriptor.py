from typing import Any
def describe_exit_sink(descriptor_input):
    if not isinstance(descriptor_input, dict): return {"exit_sink_descriptor_status": "invalid"}
    if "sink_id" not in descriptor_input or "sink_kind" not in descriptor_input: return {"exit_sink_descriptor_status": "invalid"}
    return {"exit_sink_descriptor_status": "described", "sink_id": descriptor_input.get("sink_id")}
