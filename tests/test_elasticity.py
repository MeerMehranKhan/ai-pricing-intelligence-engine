"""Tests for elasticity module."""
import pytest
from pricing_engine.models import ProductInput, CompetitorAnalysis, PositioningResult, Positioning, QualityLabel
from pricing_engine.elasticity import estimate_elasticity, compute_demand_at_price


def _make_product(**kw):
    return ProductInput(name="Test", category=kw.get("category", "electronics"), cost=kw.get("cost", 10.0))


def _make_comp(**kw):
    return CompetitorAnalysis(prices=[20, 25, 30], count=3, median=kw.get("median", 25.0), mean=25, min_price=20, max_price=30, p25=22, p75=28, crowding_index=kw.get("crowding", 0.5))


def _make_pos(segment=Positioning.MID_TIER):
    return PositioningResult(segment=segment, confidence=0.5, rationale="test")


def test_elasticity_is_negative():
    result = estimate_elasticity(_make_product(), _make_comp(), _make_pos())
    assert result.elasticity_coefficient < 0


def test_demand_decreases_with_price():
    result = estimate_elasticity(_make_product(), _make_comp(), _make_pos())
    curve = result.demand_curve
    low_price_demand = curve[0]["demand"]
    high_price_demand = curve[-1]["demand"]
    assert low_price_demand > high_price_demand


def test_demand_floor_respected():
    demand = compute_demand_at_price(1000, 25, 100, -1.5, 5.0, 300.0)
    assert demand >= 5.0


def test_demand_ceiling_respected():
    demand = compute_demand_at_price(1.0, 25, 100, -1.5, 5.0, 300.0)
    assert demand <= 300.0


def test_sensitivity_classification():
    result = estimate_elasticity(_make_product(category="electronics"), _make_comp(), _make_pos())
    assert result.sensitivity_class in ["price-sensitive", "moderate", "price-resistant"]


def test_uncertainty_varies_with_quality():
    high = estimate_elasticity(_make_product(), _make_comp(), _make_pos(), QualityLabel.HIGH)
    low = estimate_elasticity(_make_product(), _make_comp(), _make_pos(), QualityLabel.LOW)
    assert low.uncertainty_pct > high.uncertainty_pct
