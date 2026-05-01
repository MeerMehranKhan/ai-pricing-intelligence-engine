"""Tests for competitive reaction module."""
import pytest
from pricing_engine.models import CompetitorAnalysis, PositioningResult, Positioning, StrategyResult, StrategyScore, ReactionType
from pricing_engine.competitive_reaction import predict_competitive_reaction


def _make_inputs(strategy_name="Competitive Matching", crowding=0.5):
    strat_score = StrategyScore(name=strategy_name, score=65, adjusted_price=25, rationale="test")
    strategy = StrategyResult(selected=strat_score, all_scores=[strat_score])
    comp = CompetitorAnalysis(prices=[20,25,30], count=3, median=25, mean=25, min_price=20, max_price=30, p25=22, p75=28, crowding_index=crowding)
    pos = PositioningResult(segment=Positioning.MID_TIER, confidence=0.5, rationale="test")
    return strategy, comp, pos


def test_penetration_higher_likelihood():
    pen = predict_competitive_reaction(*_make_inputs("Penetration Pricing"), 20)
    comp = predict_competitive_reaction(*_make_inputs("Competitive Matching"), 25)
    assert pen.price_war_likelihood > comp.price_war_likelihood


def test_premium_low_likelihood():
    result = predict_competitive_reaction(*_make_inputs("Premium Pricing"), 35)
    assert result.likelihood_label == "Low"


def test_crowded_market_increases_risk():
    low = predict_competitive_reaction(*_make_inputs(crowding=0.2), 25)
    high = predict_competitive_reaction(*_make_inputs(crowding=0.8), 25)
    assert high.price_war_likelihood > low.price_war_likelihood


def test_mitigation_provided():
    result = predict_competitive_reaction(*_make_inputs(), 25)
    assert len(result.mitigation) > 0
