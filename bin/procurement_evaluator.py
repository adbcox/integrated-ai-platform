#!/usr/bin/env python3
"""Procurement evaluator: scores parts and makes procurement decisions."""

import json
from datetime import datetime, timedelta


def score_part(part_number: str, unit_cost: float, lead_time_days: int, availability: int) -> float:
    """Score a part based on cost, availability, and lead time."""
    # Normalize scores to 0-100
    cost_score = max(0, 100 - (unit_cost * 10))  # Lower cost = higher score
    availability_score = min(100, availability / 10)  # More available = higher score
    lead_time_score = max(0, 100 - (lead_time_days * 5))  # Shorter lead time = higher score

    # Weighted average
    total_score = (cost_score * 0.3) + (availability_score * 0.4) + (lead_time_score * 0.3)
    return round(min(100, max(0, total_score)), 2)


def evaluate_bom(bom_data: dict) -> dict:
    """Evaluate BOM and make procurement decisions."""
    project_id = bom_data.get("project_id")
    components = bom_data.get("components", [])
    total_bom_cost = bom_data.get("total_cost", 0)

    # Create product records from BOM components
    product_records = []
    procurement_decisions = []

    for component in components:
        part_number = component["part_number"]
        description = component["description"]
        quantity = component["quantity"]
        unit_cost = component["unit_cost"]
        supplier = component["supplier"]
        lead_time = component["lead_time_days"]

        # Simulate inventory levels
        current_inventory = max(0, int(quantity * 100 - (lead_time * 10)))
        availability = max(10, 100 - (lead_time * 3))

        # Score the part
        part_score = score_part(part_number, unit_cost, lead_time, availability)

        # Create product record
        product = {
            "id": f"prod-{part_number.lower().replace(' ', '-')}",
            "name": description,
            "description": f"{description} - Part: {part_number}",
            "category": "embedded" if "esp32" in part_number.lower() or "nordic" in part_number.lower() else "component",
            "specifications": {
                "supplier": supplier,
                "lead_time_days": lead_time,
                "unit_cost": unit_cost,
            },
            "search_tags": [supplier, description.split()[0], "component"],
        }
        product_records.append(product)

        # Create procurement decision
        decision = {
            "product_id": product["id"],
            "quantity": quantity,
            "current_inventory": current_inventory,
            "projected_consumption": quantity * 12,  # Assume 12-month consumption
            "decision_date": datetime.now().isoformat(),
            "reasoning": f"Score: {part_score}. Current stock: {current_inventory} units. Lead time: {lead_time} days. Availability: {availability}%",
            "recommended_quantity": max(quantity, int(quantity * 2)),  # Recommend 2x quantity
            "total_estimated_cost": round(unit_cost * quantity, 2),
            "score": part_score,
            "supplier": supplier,
            "part_number": part_number,
        }
        procurement_decisions.append(decision)

    # Sort by score
    procurement_decisions.sort(key=lambda x: x["score"], reverse=True)

    # Calculate total procurement cost
    total_procurement_cost = sum(d["total_estimated_cost"] for d in procurement_decisions)

    return {
        "project_id": project_id,
        "product_records": product_records,
        "procurement_decisions": procurement_decisions,
        "summary": {
            "total_parts": len(components),
            "total_bom_cost": total_bom_cost,
            "total_procurement_cost": round(total_procurement_cost, 2),
            "average_lead_time": round(sum(d["quantity"] * components[components.index([c for c in components if c["part_number"] == d["part_number"]][0])]["lead_time_days"] for d in procurement_decisions) / len(components), 1),
            "cost_increase": round(total_procurement_cost - total_bom_cost, 2),
        },
        "alternatives": {
            "highest_scored_parts": [d for d in procurement_decisions[:3]],
            "fastest_delivery": sorted(procurement_decisions, key=lambda x: components[[c["part_number"] for c in components].index(x["part_number"])]["lead_time_days"])[:3],
            "lowest_cost": sorted(procurement_decisions, key=lambda x: x["total_estimated_cost"])[:3],
        },
        "evaluated_at": datetime.now().isoformat(),
    }


def main():
    """Main entry point."""
    # Sample BOM from hardware processor
    sample_bom = {
        "project_id": "hw-esp32-iot-gateway-v1",
        "components": [
            {
                "part_number": "ESP32-S3-WROOM-1-N8",
                "description": "ESP32-S3 Module (esp32-s3)",
                "quantity": 1,
                "unit_cost": 4.50,
                "supplier": "Espressif",
                "lead_time_days": 5,
            },
            {
                "part_number": "AMS1117-3V3",
                "description": "3.3V Linear Regulator",
                "quantity": 1,
                "unit_cost": 0.25,
                "supplier": "AMS",
                "lead_time_days": 3,
            },
            {
                "part_number": "TDK-C1206X5R1V106M",
                "description": "Capacitor 10uF 25V 1206",
                "quantity": 5,
                "unit_cost": 0.08,
                "supplier": "TDK",
                "lead_time_days": 2,
            },
        ],
        "total_cost": 5.35,
    }

    result = evaluate_bom(sample_bom)
    print(json.dumps(result, indent=2))

    return result


if __name__ == "__main__":
    main()
