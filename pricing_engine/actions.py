"""
Action Engine and Scale Projector.

Transforms analysis into actionable next steps, platform-specific tactics,
and scale feasibility projections.
"""

from __future__ import annotations
from pricing_engine.config import CATEGORY_CONFIG
from pricing_engine.models import (
    ActionPlan, CompetitorAnalysis, ElasticityResult, PricingRecommendation,
    ProductInput, ScaleProjection, StrategyResult, UnitEconomics, ViabilitySignal,
)
from pricing_engine.utils import format_currency


def generate_action_plan(
    product: ProductInput, recommendation: PricingRecommendation,
    unit_economics: UnitEconomics, strategy: StrategyResult,
    competitor_analysis: CompetitorAnalysis, elasticity: ElasticityResult,
) -> ActionPlan:
    """Generate actionable next steps from analysis results."""
    price = recommendation.recommended_price
    strat_name = strategy.selected.name
    signal = recommendation.viability.signal

    # Primary action
    if signal == ViabilitySignal.NO_GO:
        primary = f"Do not launch at ${price:.2f}. Renegotiate supplier cost or find a different product."
    elif signal == ViabilitySignal.CAUTION:
        primary = f"Test at ${price:.2f} with limited budget before scaling. Validate demand before committing."
    else:
        primary = f"List at ${price:.2f} on {product.platform.title()} with optimized listing content."

    # Target audience
    if elasticity.sensitivity_class == "price-sensitive":
        audience = "Price-conscious buyers who compare 3-5 options before purchasing."
    elif elasticity.sensitivity_class == "price-resistant":
        audience = "Quality-focused buyers willing to pay more for perceived value."
    else:
        audience = "Value-oriented shoppers looking for the best balance of price and quality."

    # Pricing tactic
    if "Psychological" in strat_name or "Anchor" in strat_name:
        tactic = f"Use charm pricing (${price - 0.01:.2f}) with 'Compare at ${price * 1.3:.2f}' anchor."
    elif "Penetration" in strat_name:
        tactic = f"Launch at ${price:.2f} with introductory pricing. Consider raising after building reviews."
    elif "Premium" in strat_name:
        tactic = f"Position at ${price:.2f} with premium packaging and brand storytelling."
    elif "Bundle" in strat_name:
        bundle_price = price * 2.7
        tactic = f"Offer a 3-pack bundle at ${bundle_price:.2f} (save 10%) to increase order value."
    else:
        tactic = f"Price competitively at ${price:.2f} and differentiate on value, not price."

    # First test
    cac = unit_economics.cost_structure.marketing_cac
    daily_budget = round(cac * 5, 2)
    expected_conv = round(daily_budget / cac) if cac > 0 else 5
    first_test = (
        f"Run a 7-day test at ${price:.2f} with ${daily_budget:.0f}/day ad spend. "
        f"Expect {expected_conv}-{expected_conv*2} conversions to validate demand."
    )

    # Platform-specific actions
    platform_actions = _get_platform_actions(product.platform)

    # Scale projection
    scale_proj = None
    if product.target_monthly_revenue and product.target_monthly_revenue > 0:
        scale_proj = compute_scale_projection(
            product.target_monthly_revenue, price, unit_economics, elasticity,
        )

    return ActionPlan(
        primary_action=primary, target_audience=audience,
        pricing_tactic=tactic, first_test=first_test,
        signal=signal, platform_actions=platform_actions,
        scale_projection=scale_proj,
    )


def compute_scale_projection(
    target_revenue: float, price: float,
    unit_economics: UnitEconomics, elasticity: ElasticityResult,
) -> ScaleProjection:
    """Project what it takes to hit a revenue target."""
    required_volume = int(target_revenue / price) if price > 0 else 0
    cac = unit_economics.cost_structure.marketing_cac
    total_marketing = cac * required_volume
    daily_ad_spend = round(total_marketing / 30, 2)
    monthly_profit = (unit_economics.profit_after_marketing * required_volume)

    constraints: list[str] = []
    if required_volume > elasticity.demand_ceiling * 2:
        feasibility = "Unrealistic"
        constraints.append(
            f"Requires {required_volume} sales/month, which is {required_volume/elasticity.demand_base:.0f}x "
            "the estimated base demand. This volume is unlikely without dominant market share."
        )
    elif required_volume > elasticity.demand_base * 1.5:
        feasibility = "Stretch"
        constraints.append(
            f"Requires {required_volume} sales/month, above base demand of {elasticity.demand_base:.0f}. "
            "Achievable with strong marketing but challenging."
        )
    else:
        feasibility = "Achievable"
        constraints.append(
            f"Requires {required_volume} sales/month at ${price:.2f}. "
            f"This is within realistic demand range for this category."
        )

    if daily_ad_spend > 200:
        constraints.append(f"Requires ${daily_ad_spend:.0f}/day ad spend. Ensure ROAS > {price/cac:.1f}x.")

    break_even_month = None
    if monthly_profit > 0:
        setup_cost = total_marketing * 0.5
        break_even_month = max(1, int(setup_cost / monthly_profit) + 1)

    return ScaleProjection(
        target_revenue=target_revenue, required_volume=required_volume,
        required_daily_ad_spend=daily_ad_spend,
        total_monthly_marketing=round(total_marketing, 2),
        feasibility=feasibility, constraints=constraints,
        break_even_month=break_even_month,
    )


def _get_platform_actions(platform: str) -> list[str]:
    """Get platform-specific tactical actions."""
    actions = {
        "amazon": [
            "Optimize listing with backend keywords and A+ content",
            "Consider FBA for Prime badge and faster delivery",
            "Set up PPC campaigns targeting category keywords",
            "Monitor BSR (Best Seller Rank) daily for first 2 weeks",
        ],
        "shopify": [
            "Build a value-focused landing page with social proof",
            "Set up abandoned cart email sequence",
            "Install urgency elements (stock counter, limited-time offer)",
            "Set up Facebook/Instagram retargeting pixel",
        ],
        "ebay": [
            "Use auction format initially to test market price",
            "Offer combined shipping discounts for multi-item purchases",
            "Optimize title with high-search-volume keywords",
        ],
        "etsy": [
            "Invest in high-quality product photography",
            "Write story-driven product descriptions",
            "Use Etsy Ads with $5-10/day budget initially",
        ],
    }
    return actions.get(platform, [
        "Test across 2-3 channels before committing budget",
        "Start with small daily ad spend ($10-20) to validate demand",
        "Collect and display customer reviews early",
    ])
