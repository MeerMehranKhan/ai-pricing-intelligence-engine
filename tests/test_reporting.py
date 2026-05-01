"""Tests for reporting module."""
import json, pytest
from pricing_engine.reporting import export_json_bytes, export_csv_bytes, export_pdf_bytes


SAMPLE_DATA = {
    "simulation": {"price_points": [20,25,30], "demand": [120,100,80], "revenue": [2400,2500,2400], "total_cost": [2000,2100,2200], "profit": [400,400,200]},
    "recommendation": {"recommended_price": 25.0, "min_safe_price": 18.0, "max_safe_price": 35.0, "contribution_margin_pct": 0.35, "confidence_score": 65, "risk": {"level": "Medium"}, "explanations": ["Test explanation"]},
    "strategy": {"selected": {"name": "Competitive Matching", "rationale": "Test"}},
}

def test_json_export():
    data = export_json_bytes(SAMPLE_DATA)
    assert len(data) > 0
    parsed = json.loads(data)
    assert "recommendation" in parsed

def test_csv_export():
    data = export_csv_bytes(SAMPLE_DATA)
    assert len(data) > 0
    assert b"Price" in data

def test_pdf_export():
    data = export_pdf_bytes(SAMPLE_DATA, "TestProduct")
    assert len(data) > 0
