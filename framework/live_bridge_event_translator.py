from typing import Any
def translate_event(adaptation: dict[str, Any], event_vocab: dict[str, Any], translator_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(adaptation, dict) or not isinstance(event_vocab, dict) or not isinstance(translator_config, dict):
        return {"event_translation_status": "invalid_input", "translated_kind": None, "translation_vocab_id": None}
    a_ok = adaptation.get("signal_adaptation_status") == "adapted"
    if a_ok:
        return {"event_translation_status": "translated", "translated_kind": adaptation.get("adapted_signal_kind"), "translation_vocab_id": event_vocab.get("vocab_id", "vocab-0001")}
    return {"event_translation_status": "not_adapted", "translated_kind": None, "translation_vocab_id": None}
