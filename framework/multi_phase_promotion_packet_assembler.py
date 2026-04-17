from typing import Any


def assemble_promotion_packet(
    publication: dict[str, Any],
    promotion_readiness: dict[str, Any],
    assembler_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(publication, dict)
        or not isinstance(promotion_readiness, dict)
        or not isinstance(assembler_config, dict)
    ):
        return {
            "packet_assembly_status": "invalid_input",
            "assembly_phase": None,
            "packet_count": 0,
        }

    pub_ok = publication.get("publication_status") == "published"
    pr_ok = promotion_readiness.get("promotion_readiness_status") == "ready"

    if pub_ok and pr_ok:
        return {
            "packet_assembly_status": "assembled",
            "assembly_phase": publication.get("publication_phase"),
            "packet_count": 1,
        }

    return {
        "packet_assembly_status": "failed",
        "assembly_phase": None,
        "packet_count": 0,
    }
