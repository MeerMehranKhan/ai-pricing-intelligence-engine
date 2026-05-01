"""
Price Elasticity and Demand Estimation Engine.

Estimates price sensitivity using category-based heuristics adjusted for
platform, competition, and positioning. Generates demand curves with
realistic constraints (floor, ceiling, diminishing returns).
"""

from __future__ import annotations
import numpy as np
from pricing_engine.config import (
    CATEGORY_CONFIG, DEMAND_CEILING_MULTIPLIER, DEMAND_FLOOR_MULTIPLIER,
    DIMINISHING_RETURNS_THRESHOLD, PLATFORM_ELASTICITY_MODIFIER,
    UNCERTAINTY_HIGH_QUALITY, UNCERTAINTY_MED_QUALITY, UNCERTAINTY_LOW_QUALITY,
)
from pricing_engine.models import (
    CompetitorAnalysis, ElasticityResult, PositioningResult,
    ProductInput, QualityLabel,
)


def estimate_elasticity(
    product: ProductInput, competitor_analysis: CompetitorAnalysis,
    positioning: PositioningResult,
    data_quality_label: QualityLabel = QualityLabel.MEDIUM,
) -> ElasticityResult:
    """Estimate price elasticity and generate a demand curve."""
    cat_config = CATEGORY_CONFIG.get(product.category, CATEGORY_CONFIG["general"])
    warnings: list[str] = []
    base_elasticity = cat_config["elasticity"]
    platform_mod = PLATFORM_ELASTICITY_MODIFIER.get(product.platform, 1.0)
    adjusted = base_elasticity * platform_mod
    if competitor_analysis.crowding_index > 0.7:
        adjusted *= 1.15
    elif competitor_analysis.crowding_index < 0.3:
        adjusted *= 0.85
    if positioning.segment.value == "budget":
        adjusted *= 1.1
    elif positioning.segment.value == "premium":
        adjusted *= 0.8
    if product.cost > 100 and product.category != "luxury":
        adjusted *= 1.1

    abs_e = abs(adjusted)
    if abs_e > 1.5:
        sensitivity_class = "price-sensitive"
    elif abs_e >= 0.8:
        sensitivity_class = "moderate"
    else:
        sensitivity_class = "price-resistant"

    demand_base = float(cat_config.get("demand_base", 120))
    demand_ceiling = demand_base * DEMAND_CEILING_MULTIPLIER
    demand_floor = demand_base * DEMAND_FLOOR_MULTIPLIER
    p_ref = competitor_analysis.median if competitor_analysis.median > 0 else product.cost * 2.0

    price_points = np.linspace(p_ref * 0.5, p_ref * 2.0, 50)
    demand_curve = []
    for p in price_points:
        raw_demand = compute_demand_at_price(p, p_ref, demand_base, adjusted, demand_floor, demand_ceiling)
        demand_curve.append({"price": round(float(p), 2), "demand": round(float(raw_demand), 1)})

    uncertainty_map = {
        QualityLabel.HIGH: UNCERTAINTY_HIGH_QUALITY,
        QualityLabel.MEDIUM: UNCERTAINTY_MED_QUALITY,
        QualityLabel.LOW: UNCERTAINTY_LOW_QUALITY,
    }
    uncertainty = uncertainty_map.get(data_quality_label, UNCERTAINTY_MED_QUALITY)
    warnings.append("Elasticity estimate is based on category averages, not product-specific data.")
    if data_quality_label == QualityLabel.LOW:
        warnings.append("High uncertainty. Treat demand estimates as directional, not precise.")

    return ElasticityResult(
        elasticity_coefficient=round(adjusted, 3),
        sensitivity_class=sensitivity_class,
        demand_base=demand_base,
        demand_curve=demand_curve,
        demand_ceiling=demand_ceiling,
        demand_floor=demand_floor,
        uncertainty_pct=uncertainty,
        assumption_warnings=warnings,
    )


def compute_demand_at_price(
    price: float, reference_price: float, demand_base: float,
    elasticity: float, demand_floor: float, demand_ceiling: float,
) -> float:
    """Compute estimated demand at a given price using power-law model with constraints."""
    if price <= 0 or reference_price <= 0:
        return demand_base
    price_ratio = price / reference_price
    raw_demand = demand_base * (price_ratio ** elasticity)
    if price_ratio < DIMINISHING_RETURNS_THRESHOLD:
        threshold_demand = demand_base * (DIMINISHING_RETURNS_THRESHOLD ** elasticity)
        log_factor = np.log1p((DIMINISHING_RETURNS_THRESHOLD - price_ratio) * 5)
        raw_demand = threshold_demand + (demand_ceiling - threshold_demand) * (log_factor / (1 + log_factor))
    return float(np.clip(raw_demand, demand_floor, demand_ceiling))
