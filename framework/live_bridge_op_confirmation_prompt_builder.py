from typing import Any
def build_confirmation_prompt(prompt_input):
    if not isinstance(prompt_input, dict): return {"op_confirmation_prompt_status": "invalid"}
    if "command_id" not in prompt_input: return {"op_confirmation_prompt_status": "invalid"}
    return {"op_confirmation_prompt_status": "built", "command_id": prompt_input.get("command_id")}
