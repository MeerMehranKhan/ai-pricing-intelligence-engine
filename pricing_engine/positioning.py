"""
Market Positioning Engine.

Determines whether a product should be positioned as Budget, Mid-tier,
or Premium based on cost structure, competitor landscape, and elasticity.
Enforces consistency between positioning, strategy, and pricing.
"""

from __future__ import annotations

from pricing_engine.config import CATEGORY_CONFIG, POSITIONING_MULTIPLIERS
from pricing_engine.models import (
    CompetitorAnalysis,
    Positioning,
    PositioningResult,
    ProductInput,
    UnitEconomics,
)


def determine_positioning(
    product: ProductInput,
    competitor_analysis: CompetitorAnalysis,
    unit_economics: UnitEconomics,
) -> PositioningResult:
    """Determine the optimal market positioning for a product.

    Considers cost structure, competitor landscape, and user preference.
    Validates that the chosen positioning is compatible with the product's
    economics. If the user requests a positioning that conflicts with
    reality, it warns but respects the override.

    Args:
        product: Validated product input.
        competitor_analysis: Competitor pricing analysis results.
        unit_economics: Unit economics at a reference price.

    Returns:
        PositioningResult with segment, rationale, and alignment checks.
    """
    warnings: list[str] = []
    user_override = False

    # Score each positioning
    budget_score = _score_budget(product, competitor_analysis, unit_economics)
    mid_score = _score_mid(product, competitor_analysis, unit_economics)
    premium_score = _score_premium(product, competitor_analysis, unit_economics)

    scores = {
        Positioning.BUDGET: budget_score,
        Positioning.MID_TIER: mid_score,
        Positioning.PREMIUM: premium_score,
    }

    # Auto-determine best positioning
    auto_positioning = max(scores, key=scores.get)
    confidence = scores[auto_positioning] / sum(scores.values()) if sum(scores.values()) > 0 else 0.33

    # Handle user preference
    if product.positioning:
        requested = Positioning(product.positioning)
        if requested != auto_positioning:
            user_override = True
            # Check if user preference is viable
            cost_compatible = _check_cost_compatibility(
                requested, product, competitor_analysis
            )
            if not cost_compatible:
                warnings.append(
                    f"Your costs may not support {requested.value} positioning at viable margins. "
                    f"Auto-analysis suggests {auto_positioning.value} positioning instead."
                )
            else:
                warnings.append(
                    f"Using your preferred {requested.value} positioning "
                    f"(auto-analysis suggested {auto_positioning.value})."
                )
            final_positioning = requested
        else:
            final_positioning = auto_positioning
    else:
        final_positioning = auto_positioning

    rationale = _build_rationale(
        final_positioning, product, competitor_analysis, scores
    )

    return PositioningResult(
        segment=final_positioning,
        confidence=round(confidence, 2),
        rationale=rationale,
        alignment_warnings=warnings,
        cost_compatible=_check_cost_compatibility(
            final_positioning, product, competitor_analysis
        ),
        user_override=user_override,
    )


def _score_budget(
    product: ProductInput,
    comp: CompetitorAnalysis,
    econ: UnitEconomics,
) -> float:
    """Score budget positioning viability."""
    score = 33.0  # Base

    # Budget works when costs are low relative to market
    if comp.median > 0:
        cost_ratio = product.cost / comp.median
        if cost_ratio < 0.3:
            score += 20
        elif cost_ratio < 0.5:
            score += 10

    # Budget works in crowded markets
    if comp.crowding_index > 0.6:
        score += 10

    # Budget is harder with high all-in costs
    if econ.contribution_margin_pct < 0.20:
        score -= 15

    return max(0, score)


def _score_mid(
    product: ProductInput,
    comp: CompetitorAnalysis,
    econ: UnitEconomics,
) -> float:
    """Score mid-tier positioning viability."""
    score = 40.0  # Slightly favored as default

    # Mid works when cost is moderate
    if comp.median > 0:
        cost_ratio = product.cost / comp.median
        if 0.3 <= cost_ratio <= 0.6:
            score += 15

    # Mid is the safe bet in most markets
    if 0.3 <= comp.crowding_index <= 0.7:
        score += 10

    # Good margins support mid-tier
    if 0.25 <= econ.contribution_margin_pct <= 0.55:
        score += 10

    return score


def _score_premium(
    product: ProductInput,
    comp: CompetitorAnalysis,
    econ: UnitEconomics,
) -> float:
    """Score premium positioning viability."""
    score = 27.0  # Base

    cat_config = CATEGORY_CONFIG.get(product.category, CATEGORY_CONFIG["general"])

    # Premium works in less crowded markets
    if comp.crowding_index < 0.4:
        score += 15

    # Premium works with low elasticity categories
    if abs(cat_config.get("elasticity", -1.3)) < 1.0:
        score += 15

    # Premium needs healthy margins
    if econ.contribution_margin_pct > 0.45:
        score += 10

    # Premium has room if gaps exist at high end
    for gap in comp.gaps:
        if gap.get("high", 0) > comp.p75:
            score += 10
            break

    return score


def _check_cost_compatibility(
    positioning: Positioning,
    product: ProductInput,
    comp: CompetitorAnalysis,
) -> bool:
    """Check if cost structure supports the chosen positioning."""
    if comp.median == 0:
        return True

    multipliers = POSITIONING_MULTIPLIERS[positioning.value]
    target_price = comp.median * multipliers["target"]
    min_viable = product.cost * 1.15  # At least 15% gross margin

    return target_price >= min_viable


def _build_rationale(
    positioning: Positioning,
    product: ProductInput,
    comp: CompetitorAnalysis,
    scores: dict[Positioning, float],
) -> str:
    """Build a human-readable rationale for the positioning decision."""
    total = sum(scores.values())
    pcts = {k: round(v / total * 100) for k, v in scores.items()} if total > 0 else {}

    if positioning == Positioning.BUDGET:
        return (
            f"Budget positioning selected (score: {pcts.get(Positioning.BUDGET, 0)}%). "
            f"Your cost structure (${product.cost:.2f}) allows competitive pricing "
            f"below the market median of ${comp.median:.2f}. "
            "This is suitable for price-sensitive markets with high competition."
        )
    elif positioning == Positioning.PREMIUM:
        return (
            f"Premium positioning selected (score: {pcts.get(Positioning.PREMIUM, 0)}%). "
            f"The market shows room for premium pricing above ${comp.p75:.2f}. "
            "Lower competition density and category characteristics support this positioning."
        )
    else:
        return (
            f"Mid-tier positioning selected (score: {pcts.get(Positioning.MID_TIER, 0)}%). "
            f"Your product fits well near the market median of ${comp.median:.2f}. "
            "This balances competitiveness with healthy margins."
        )
