from typing import Any

def normalize_directive(directive_receipt: dict, schema: dict, normalize_config: dict) -> dict:
    if not isinstance(directive_receipt, dict) or not isinstance(schema, dict) or not isinstance(normalize_config, dict):
        return {"directive_normalization_status": "invalid_input"}
    if directive_receipt.get("directive_receipt_status") != "received":
        return {"directive_normalization_status": "no_receipt"}
    return {
        "directive_normalization_status": "normalized",
        "normalized_directive_id": directive_receipt.get("received_directive_id"),
        "normalized_kind": directive_receipt.get("received_directive_kind"),
        "normalized_schema_id": schema.get("schema_id", "dsch-0001"),
    }
