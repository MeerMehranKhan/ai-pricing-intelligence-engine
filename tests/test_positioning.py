"""Tests for positioning module."""
import pytest
from pricing_engine.models import ProductInput, CompetitorAnalysis, UnitEconomics, CostStructure, Positioning
from pricing_engine.positioning import determine_positioning


def _make_inputs(cost=10, median=25, crowding=0.5, margin_pct=0.35):
    product = ProductInput(name="Test", category="electronics", cost=cost)
    comp = CompetitorAnalysis(prices=[20,25,30], count=3, median=median, mean=25, min_price=20, max_price=30, p25=22, p75=28, crowding_index=crowding, gaps=[])
    cs = CostStructure(cogs=cost, shipping=3, packaging=1, platform_fee=3, processing_fee=1, returns_buffer=1, marketing_cac=10)
    econ = UnitEconomics(price=median, all_in_cost=cost+4, variable_cost_per_sale=cost+8, contribution_margin=median-(cost+8), contribution_margin_pct=margin_pct, break_even_cac=5, target_cac=1.5, profit_after_marketing=-5, cost_structure=cs)
    return product, comp, econ


def test_returns_positioning():
    result = determine_positioning(*_make_inputs())
    assert result.segment in [Positioning.BUDGET, Positioning.MID_TIER, Positioning.PREMIUM]


def test_user_override():
    product, comp, econ = _make_inputs()
    product.positioning = "premium"
    result = determine_positioning(product, comp, econ)
    assert result.segment == Positioning.PREMIUM
    assert result.user_override


def test_cost_compatibility_warning():
    product, comp, econ = _make_inputs(cost=30, median=25)
    product.positioning = "budget"
    result = determine_positioning(product, comp, econ)
    assert not result.cost_compatible or len(result.alignment_warnings) > 0
