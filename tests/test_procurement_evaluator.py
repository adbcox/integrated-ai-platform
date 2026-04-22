#!/usr/bin/env python3
"""Tests for procurement evaluator."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "bin"))

from procurement_evaluator import evaluate_bom, score_part


def test_part_scoring():
    """Test part scoring function."""
    # Test basic scoring
    score1 = score_part("PART-001", unit_cost=1.0, lead_time_days=3, availability=50)
    score2 = score_part("PART-002", unit_cost=100.0, lead_time_days=10, availability=20)

    assert 0 <= score1 <= 100
    assert 0 <= score2 <= 100
    # Lower cost should result in higher score
    assert score1 > score2

    print("✓ test_part_scoring passed")


def test_bom_evaluation():
    """Test BOM evaluation."""
    sample_bom = {
        "project_id": "hw-test-v1",
        "components": [
            {
                "part_number": "PART-001",
                "description": "Component 1",
                "quantity": 1,
                "unit_cost": 10.0,
                "supplier": "Supplier A",
                "lead_time_days": 5,
            },
            {
                "part_number": "PART-002",
                "description": "Component 2",
                "quantity": 2,
                "unit_cost": 5.0,
                "supplier": "Supplier B",
                "lead_time_days": 3,
            },
        ],
        "total_cost": 20.0,
    }

    result = evaluate_bom(sample_bom)

    assert result["project_id"] == "hw-test-v1"
    assert len(result["product_records"]) == 2
    assert len(result["procurement_decisions"]) == 2
    assert "summary" in result
    assert "alternatives" in result

    # Verify summary
    summary = result["summary"]
    assert summary["total_parts"] == 2
    assert summary["total_bom_cost"] == 20.0
    assert summary["total_procurement_cost"] > 0

    print("✓ test_bom_evaluation passed")


def test_procurement_decision_structure():
    """Test procurement decision has required fields."""
    sample_bom = {
        "project_id": "hw-test",
        "components": [
            {
                "part_number": "PART-001",
                "description": "Test Part",
                "quantity": 1,
                "unit_cost": 5.0,
                "supplier": "Supplier",
                "lead_time_days": 3,
            }
        ],
        "total_cost": 5.0,
    }

    result = evaluate_bom(sample_bom)
    decision = result["procurement_decisions"][0]

    required_fields = [
        "product_id",
        "quantity",
        "current_inventory",
        "projected_consumption",
        "decision_date",
        "reasoning",
        "recommended_quantity",
        "total_estimated_cost",
        "score",
        "supplier",
        "part_number",
    ]

    for field in required_fields:
        assert field in decision, f"Missing field: {field}"

    print("✓ test_procurement_decision_structure passed")


def test_product_record_structure():
    """Test product record structure."""
    sample_bom = {
        "project_id": "hw-test",
        "components": [
            {
                "part_number": "ESP32-TEST",
                "description": "Test ESP32",
                "quantity": 1,
                "unit_cost": 4.5,
                "supplier": "Espressif",
                "lead_time_days": 5,
            }
        ],
        "total_cost": 4.5,
    }

    result = evaluate_bom(sample_bom)
    product = result["product_records"][0]

    required_fields = ["id", "name", "description", "category", "specifications", "search_tags"]

    for field in required_fields:
        assert field in product

    assert product["category"] in ["embedded", "component"]

    print("✓ test_product_record_structure passed")


def test_alternatives_generation():
    """Test that alternatives are generated."""
    sample_bom = {
        "project_id": "hw-test",
        "components": [
            {
                "part_number": f"PART-{i:03d}",
                "description": f"Part {i}",
                "quantity": 1,
                "unit_cost": 5.0 + i,
                "supplier": f"Supplier {i}",
                "lead_time_days": 3 + i,
            }
            for i in range(5)
        ],
        "total_cost": 30.0,
    }

    result = evaluate_bom(sample_bom)
    alternatives = result["alternatives"]

    assert "highest_scored_parts" in alternatives
    assert "fastest_delivery" in alternatives
    assert "lowest_cost" in alternatives

    assert len(alternatives["highest_scored_parts"]) <= 3
    assert len(alternatives["fastest_delivery"]) <= 3
    assert len(alternatives["lowest_cost"]) <= 3

    print("✓ test_alternatives_generation passed")


def test_sorting_by_score():
    """Test that procurement decisions are sorted by score."""
    sample_bom = {
        "project_id": "hw-test",
        "components": [
            {
                "part_number": "CHEAP",
                "description": "Cheap part",
                "quantity": 1,
                "unit_cost": 1.0,
                "supplier": "Supplier",
                "lead_time_days": 10,
            },
            {
                "part_number": "EXPENSIVE",
                "description": "Expensive part",
                "quantity": 1,
                "unit_cost": 100.0,
                "supplier": "Supplier",
                "lead_time_days": 2,
            },
        ],
        "total_cost": 101.0,
    }

    result = evaluate_bom(sample_bom)
    decisions = result["procurement_decisions"]

    # First decision should have higher score
    assert decisions[0]["score"] >= decisions[1]["score"]

    print("✓ test_sorting_by_score passed")


if __name__ == "__main__":
    test_part_scoring()
    test_bom_evaluation()
    test_procurement_decision_structure()
    test_product_record_structure()
    test_alternatives_generation()
    test_sorting_by_score()

    print("\n✅ All procurement evaluator tests passed!")
