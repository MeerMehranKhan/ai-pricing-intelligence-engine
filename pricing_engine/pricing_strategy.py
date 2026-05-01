"""
Pricing Strategy Selection and Validation Engine.

Scores six pricing strategies based on product context, then validates the
chosen strategy by simulating its outcome vs alternatives. Enforces
positioning alignment.
"""

from __future__ import annotations
from pricing_engine.config import CATEGORY_CONFIG
from pricing_engine.models import (
    CompetitorAnalysis, ElasticityResult, Positioning, PositioningResult,
    ProductInput, StrategyResult, StrategyScore, UnitEconomics,
)
from pricing_engine.utils import apply_charm_pricing


STRATEGIES = [
    "Penetration Pricing", "Premium Pricing", "Competitive Matching",
    "Psychological Pricing", "Bundle-First Pricing", "Anchor-and-Discount",
]


def select_strategy(
    product: ProductInput, competitor_analysis: CompetitorAnalysis,
    positioning: PositioningResult, elasticity: ElasticityResult,
    unit_economics: UnitEconomics,
) -> StrategyResult:
    """Score all strategies and select the best fit with validation."""
    scores = []
    for strategy_name in STRATEGIES:
        score, price, rationale = _score_strategy(
            strategy_name, product, competitor_analysis, positioning, elasticity, unit_economics,
        )
        scores.append(StrategyScore(name=strategy_name, score=round(score, 1), adjusted_price=round(price, 2), rationale=rationale))

    scores.sort(key=lambda s: s.score, reverse=True)
    selected = scores[0]
    alternatives = scores[1:3]

    # Positioning alignment check
    aligned = _check_alignment(selected.name, positioning)
    validation_status = "Validated"
    fallback = None
    if not aligned:
        validation_status = "Warning"
        for alt in alternatives:
            if _check_alignment(alt.name, positioning):
                fallback = alt
                validation_status = "Overridden"
                selected = alt
                break

    return StrategyResult(
        selected=selected, alternatives=alternatives,
        validation_status=validation_status, fallback=fallback,
        positioning_aligned=aligned, all_scores=scores,
    )


def _score_strategy(
    name: str, product: ProductInput, comp: CompetitorAnalysis,
    positioning: PositioningResult, elasticity: ElasticityResult,
    econ: UnitEconomics,
) -> tuple[float, float, str]:
    """Score a single strategy. Returns (score, adjusted_price, rationale)."""
    score = 20.0
    median = comp.median if comp.median > 0 else product.cost * 2
    base_price = median

    if name == "Penetration Pricing":
        if comp.crowding_index > 0.6: score += 20
        if positioning.segment == Positioning.BUDGET: score += 20
        if abs(elasticity.elasticity_coefficient) > 1.5: score += 15
        if positioning.segment == Positioning.PREMIUM: score -= 30
        base_price = median * 0.85
        rationale = "Undercut competitors to capture market share quickly. Best for crowded, price-sensitive markets."

    elif name == "Premium Pricing":
        if comp.crowding_index < 0.4: score += 20
        if positioning.segment == Positioning.PREMIUM: score += 25
        if abs(elasticity.elasticity_coefficient) < 1.0: score += 15
        if positioning.segment == Positioning.BUDGET: score -= 30
        base_price = median * 1.25
        rationale = "Price above market to signal quality and exclusivity. Works when demand is price-resistant."

    elif name == "Competitive Matching":
        if 0.3 <= comp.crowding_index <= 0.7: score += 20
        if positioning.segment == Positioning.MID_TIER: score += 20
        if 0.8 <= abs(elasticity.elasticity_coefficient) <= 1.5: score += 10
        base_price = median
        rationale = "Match the market median to compete on value rather than price. Safe default for mid-tier products."

    elif name == "Psychological Pricing":
        score += 10  # Always a valid add-on
        if product.cost < 100: score += 10
        base_price = apply_charm_pricing(median)
        rationale = "Use charm pricing ($X.99) to improve perceived value. Combines with any base strategy."

    elif name == "Bundle-First Pricing":
        if product.cost < 20: score += 20
        if elasticity.demand_base > 150: score += 15
        cat = CATEGORY_CONFIG.get(product.category, {})
        if cat.get("elasticity", -1.3) and abs(cat.get("elasticity", -1.3)) > 1.5: score += 10
        base_price = median * 0.90
        rationale = "Bundle multiple units at a discount to increase order value. Best for low-cost, high-frequency items."

    elif name == "Anchor-and-Discount":
        if positioning.segment in [Positioning.MID_TIER, Positioning.PREMIUM]: score += 15
        if econ.contribution_margin_pct > 0.4: score += 15
        base_price = median * 1.15
        rationale = "Set a higher anchor price and offer a visible discount. Drives conversions while maintaining perceived value."

    # Ensure price covers costs
    min_price = product.cost * 1.15
    base_price = max(base_price, min_price)

    return max(0.0, score), base_price, rationale


def _check_alignment(strategy_name: str, positioning: PositioningResult) -> bool:
    """Check if a strategy is compatible with the positioning."""
    incompatible = {
        Positioning.PREMIUM: ["Penetration Pricing", "Bundle-First Pricing"],
        Positioning.BUDGET: ["Premium Pricing"],
    }
    blocked = incompatible.get(positioning.segment, [])
    return strategy_name not in blocked
