"""
Competitive Reaction Modeling.

Predicts how competitors might respond to your pricing strategy.
Uses simple heuristics based on market crowding, strategy type, and
price positioning relative to the market.
"""

from __future__ import annotations
from pricing_engine.models import (
    CompetitorAnalysis, CompetitiveReaction, PositioningResult, ReactionType, StrategyResult,
)


def predict_competitive_reaction(
    strategy: StrategyResult, competitor_analysis: CompetitorAnalysis,
    positioning: PositioningResult, recommended_price: float,
) -> CompetitiveReaction:
    """Predict likely competitive response to the chosen pricing strategy."""
    strategy_name = strategy.selected.name
    crowding = competitor_analysis.crowding_index
    median = competitor_analysis.median

    # Base reaction by strategy type
    if strategy_name in ["Penetration Pricing", "Bundle-First Pricing"]:
        base_likelihood = 0.55
        reaction = ReactionType.PRICE_MATCH
        response = "Competitors in crowded markets often match or beat new low prices within 2-4 weeks."
        time_h = "Expected within 2-4 weeks"
        mitigation = "Build brand value and customer loyalty before competitors react. Consider subscriptions or bundles to lock in customers."
    elif strategy_name == "Premium Pricing":
        base_likelihood = 0.12
        reaction = ReactionType.IGNORE
        response = "Competitors typically ignore premium entrants unless you capture significant share."
        time_h = "Unlikely in short term"
        mitigation = "Maintain quality signaling and invest in brand differentiation to sustain premium positioning."
    elif strategy_name == "Anchor-and-Discount":
        base_likelihood = 0.25
        reaction = ReactionType.FEATURE_COMPETITION
        response = "Competitors may enhance their own perceived value through bundles or features."
        time_h = "Gradual over 4-8 weeks"
        mitigation = "Keep discount structure dynamic and test different anchor points regularly."
    else:
        base_likelihood = 0.22
        reaction = ReactionType.IGNORE
        response = "Matching the market is unlikely to trigger aggressive responses."
        time_h = "Unlikely in short term"
        mitigation = "Focus on value differentiation beyond price to build sustainable advantage."

    # Adjust for crowding
    if crowding > 0.7:
        base_likelihood *= 1.3
    elif crowding < 0.3:
        base_likelihood *= 0.6

    # Adjust for undercutting
    if median > 0 and recommended_price < median * 0.85:
        base_likelihood *= 1.25
        if reaction == ReactionType.IGNORE:
            reaction = ReactionType.PRICE_MATCH

    # Adjust for few dominant competitors
    if competitor_analysis.count <= 3 and competitor_analysis.count > 0:
        base_likelihood *= 1.2

    likelihood = min(0.95, max(0.05, base_likelihood))
    if likelihood >= 0.5:
        label = "High"
    elif likelihood >= 0.25:
        label = "Medium"
    else:
        label = "Low"

    return CompetitiveReaction(
        reaction_type=reaction, price_war_likelihood=round(likelihood, 2),
        likelihood_label=label, expected_response=response,
        time_horizon=time_h, mitigation=mitigation,
    )
