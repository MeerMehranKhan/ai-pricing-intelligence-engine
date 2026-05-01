"""Tests for recommendations module."""
import pytest
from pricing_engine.models import *
from pricing_engine.recommendations import build_recommendation


def _make_full_inputs():
    product = ProductInput(name="Test", category="electronics", cost=10.0, platform="amazon")
    cs = CostStructure(cogs=10, shipping=3, packaging=1, platform_fee=3.75, processing_fee=1.17, returns_buffer=2, marketing_cac=12)
    econ = UnitEconomics(price=25, all_in_cost=14, variable_cost_per_sale=20.92, contribution_margin=4.08, contribution_margin_pct=0.163, break_even_cac=4.08, target_cac=1.22, profit_after_marketing=-7.92, cost_structure=cs)
    comp = CompetitorAnalysis(prices=[20,25,30], count=3, median=25, mean=25, min_price=20, max_price=30, p25=22, p75=28)
    pos = PositioningResult(segment=Positioning.MID_TIER, confidence=0.6, rationale="test")
    elast = ElasticityResult(elasticity_coefficient=-1.5, sensitivity_class="moderate", demand_base=100, demand_ceiling=300, demand_floor=5, uncertainty_pct=0.15)
    strat_score = StrategyScore(name="Competitive Matching", score=65, adjusted_price=25, rationale="test")
    strategy = StrategyResult(selected=strat_score, all_scores=[strat_score])
    sim = ProfitSimulation(price_points=[20,25,30], demand=[120,100,80], revenue=[2400,2500,2400], total_cost=[2000,2100,2200], profit=[400,400,200], max_profit=400, max_profit_price=22, break_even_price=15)
    dq = DataQualityReport(score=60, label=QualityLabel.MEDIUM)
    cal = CalibrationResult()
    sens = SensitivityResult(stability_score=65, fragility_label=FragilityLabel.MODERATE, base_profit=400, best_case_profit=600, worst_case_profit=100)
    react = CompetitiveReaction()
    return product, econ, comp, pos, elast, strategy, sim, dq, cal, sens, react


def test_recommendation_price_positive():
    rec = build_recommendation(*_make_full_inputs())
    assert rec.recommended_price > 0


def test_safe_range():
    rec = build_recommendation(*_make_full_inputs())
    assert rec.min_safe_price < rec.recommended_price
    assert rec.max_safe_price > rec.recommended_price


def test_confidence_score_range():
    rec = build_recommendation(*_make_full_inputs())
    assert 0 <= rec.confidence_score <= 100


def test_risk_level_valid():
    rec = build_recommendation(*_make_full_inputs())
    assert rec.risk.level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH]
