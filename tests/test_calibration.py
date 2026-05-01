"""Tests for calibration module."""
import pytest
from pricing_engine.models import ProductInput, UnitEconomics, CostStructure
from pricing_engine.calibration import calibrate


def _make_inputs(margin_pct=0.35, price=25.0, cac=12.0, category="electronics"):
    product = ProductInput(name="Test", category=category, cost=10.0)
    cs = CostStructure(cogs=10, shipping=3, packaging=1, platform_fee=3, processing_fee=1, returns_buffer=1, marketing_cac=cac)
    econ = UnitEconomics(price=price, all_in_cost=14, variable_cost_per_sale=19, contribution_margin=price-19, contribution_margin_pct=margin_pct, break_even_cac=5, target_cac=1.5, profit_after_marketing=-7, cost_structure=cs)
    return product, econ


def test_normal_range_no_flags():
    p, e = _make_inputs(margin_pct=0.25, price=50.0, cac=12.0)
    result = calibrate(p, e)
    # Electronics margin range 15-30%, so 25% should be in range
    assert result.margin_in_range


def test_high_margin_flagged():
    p, e = _make_inputs(margin_pct=0.85)
    result = calibrate(p, e)
    assert not result.margin_in_range
    assert len(result.flags) > 0


def test_high_price_flagged():
    p, e = _make_inputs(price=600.0)
    result = calibrate(p, e)
    assert not result.price_in_range


def test_low_cac_flagged():
    p, e = _make_inputs(cac=2.0)
    result = calibrate(p, e)
    assert not result.cac_in_range


def test_revenue_cap():
    p, e = _make_inputs()
    result = calibrate(p, e, projected_monthly_revenue=100000)
    assert not result.revenue_realistic
