"""
Real-World Calibration Layer.

Validates engine outputs against category benchmarks to prevent
unrealistic recommendations. Flags margins, prices, CAC, and revenue
projections that fall outside typical industry ranges.
"""

from __future__ import annotations
from pricing_engine.config import CATEGORY_CONFIG, REVENUE_NORM_MULTIPLIER_CAP
from pricing_engine.models import CalibrationResult, ProductInput, UnitEconomics


def calibrate(
    product: ProductInput, unit_economics: UnitEconomics, projected_monthly_revenue: float = 0.0,
) -> CalibrationResult:
    """Run calibration checks against category benchmarks."""
    cat = CATEGORY_CONFIG.get(product.category, CATEGORY_CONFIG["general"])
    flags: list[str] = []
    adjustments: dict[str, float] = {}
    margin_range = cat["typical_margin"]
    price_band = cat["typical_price_band"]
    cac_range = cat["typical_cac"]
    revenue_norm = cat["monthly_revenue_norm"]

    margin_ok = margin_range[0] <= unit_economics.contribution_margin_pct <= margin_range[1]
    if not margin_ok:
        if unit_economics.contribution_margin_pct > margin_range[1]:
            flags.append(
                f"This margin ({unit_economics.contribution_margin_pct*100:.0f}%) is unusually "
                f"high for {product.category}. Typical range is "
                f"{margin_range[0]*100:.0f}%-{margin_range[1]*100:.0f}%."
            )
        elif unit_economics.contribution_margin_pct < margin_range[0]:
            flags.append(
                f"This margin ({unit_economics.contribution_margin_pct*100:.0f}%) is below "
                f"the typical range for {product.category} "
                f"({margin_range[0]*100:.0f}%-{margin_range[1]*100:.0f}%)."
            )

    price_ok = price_band[0] <= unit_economics.price <= price_band[1]
    if not price_ok:
        if unit_economics.price > price_band[1]:
            flags.append(
                f"Your pricing (${unit_economics.price:.2f}) exceeds the realistic market "
                f"ceiling (${price_band[1]:.2f}) for {product.category}."
            )
        elif unit_economics.price < price_band[0]:
            flags.append(
                f"Your pricing (${unit_economics.price:.2f}) is below the typical floor "
                f"(${price_band[0]:.2f}) for {product.category}."
            )

    cac = unit_economics.cost_structure.marketing_cac
    cac_ok = cac_range[0] <= cac <= cac_range[1]
    if not cac_ok and cac > 0:
        if cac < cac_range[0]:
            flags.append(
                f"Estimated CAC (${cac:.2f}) is below the typical range "
                f"(${cac_range[0]:.0f}-${cac_range[1]:.0f}) for this category. May be optimistic."
            )
        elif cac > cac_range[1]:
            flags.append(
                f"Estimated CAC (${cac:.2f}) exceeds the typical range "
                f"(${cac_range[0]:.0f}-${cac_range[1]:.0f}). Customer acquisition may be expensive."
            )

    rev_ok = True
    if projected_monthly_revenue > revenue_norm * REVENUE_NORM_MULTIPLIER_CAP:
        rev_ok = False
        flags.append(
            f"Projected monthly revenue exceeds typical SKU performance by "
            f"{projected_monthly_revenue/revenue_norm:.1f}x."
        )

    return CalibrationResult(
        flags=flags, margin_in_range=margin_ok, price_in_range=price_ok,
        cac_in_range=cac_ok, revenue_realistic=rev_ok, adjustments=adjustments,
    )
