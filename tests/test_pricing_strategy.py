"""Tests for pricing strategy module."""
import pytest
from pricing_engine.models import ProductInput, CompetitorAnalysis, PositioningResult, Positioning, ElasticityResult, UnitEconomics, CostStructure
from pricing_engine.pricing_strategy import select_strategy


def _make_inputs(positioning=Positioning.MID_TIER, crowding=0.5, elasticity=-1.3):
    product = ProductInput(name="Test", category="electronics", cost=10.0)
    comp = CompetitorAnalysis(prices=[20,25,30], count=3, median=25, mean=25, min_price=20, max_price=30, p25=22, p75=28, crowding_index=crowding)
    pos = PositioningResult(segment=positioning, confidence=0.5, rationale="test")
    elast = ElasticityResult(elasticity_coefficient=elasticity, sensitivity_class="moderate", demand_base=100, demand_ceiling=300, demand_floor=5, uncertainty_pct=0.15)
    cs = CostStructure(cogs=10, shipping=3, packaging=1, platform_fee=3.75, processing_fee=1.17, returns_buffer=2, marketing_cac=12)
    econ = UnitEconomics(price=25, all_in_cost=14, variable_cost_per_sale=20.92, contribution_margin=4.08, contribution_margin_pct=0.163, break_even_cac=4.08, target_cac=1.22, profit_after_marketing=-7.92, cost_structure=cs)
    return product, comp, pos, elast, econ


def test_strategy_returns_result():
    result = select_strategy(*_make_inputs())
    assert result.selected is not None
    assert result.selected.score > 0


def test_premium_blocked_for_budget():
    result = select_strategy(*_make_inputs(positioning=Positioning.BUDGET))
    assert result.selected.name != "Premium Pricing"


def test_penetration_blocked_for_premium():
    result = select_strategy(*_make_inputs(positioning=Positioning.PREMIUM))
    assert result.selected.name != "Penetration Pricing"


def test_all_scores_populated():
    result = select_strategy(*_make_inputs())
    assert len(result.all_scores) == 6


def test_alternatives_populated():
    result = select_strategy(*_make_inputs())
    assert len(result.alternatives) >= 1
