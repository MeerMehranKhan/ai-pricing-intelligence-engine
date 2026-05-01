"""
Unit Economics Engine.

Computes the full cost structure for a product sale, including COGS, shipping,
packaging, platform fees, payment processing, returns buffer, and marketing CAC.
All downstream simulations use these fully-loaded costs rather than just COGS.
"""

from __future__ import annotations

from pricing_engine.config import (
    CATEGORY_CONFIG,
    PLATFORM_FEES,
    PAYMENT_PROCESSING_FEES,
    SHIPPING_COSTS,
)
from pricing_engine.models import CostStructure, ProductInput, UnitEconomics
from pricing_engine.utils import safe_divide


def compute_cost_structure(product: ProductInput, price: float) -> CostStructure:
    """Build the full cost structure for a product at a given price point.

    Uses user-provided overrides where available, otherwise falls back to
    category and platform defaults from config.

    Args:
        product: Validated product input.
        price: The selling price to compute fees against.

    Returns:
        CostStructure with all cost components and source tags.
    """
    cat_config = CATEGORY_CONFIG.get(product.category, CATEGORY_CONFIG["general"])
    platform_config = PLATFORM_FEES.get(product.platform, PLATFORM_FEES["general"])
    proc_config = PAYMENT_PROCESSING_FEES["default"]
    sources: dict[str, str] = {}

    # COGS
    cogs = product.cost
    sources["cogs"] = "deterministic"

    # Shipping
    if product.shipping_cost is not None:
        shipping = product.shipping_cost
        sources["shipping"] = "deterministic"
    else:
        weight = cat_config.get("shipping_weight", "medium")
        region = "domestic" if product.market in ["United States", "Canada"] else "international"
        shipping = SHIPPING_COSTS.get(region, SHIPPING_COSTS["domestic"]).get(weight, 5.50)
        sources["shipping"] = "estimated"

    # Packaging
    if product.packaging_cost is not None:
        packaging = product.packaging_cost
        sources["packaging"] = "deterministic"
    else:
        packaging = cat_config.get("packaging_cost", 2.00)
        sources["packaging"] = "estimated"

    # Platform fee (percentage of price + fixed fee)
    platform_fee = price * platform_config["rate"] + platform_config["fixed"]
    sources["platform_fee"] = "deterministic"

    # Payment processing
    processing_fee = price * proc_config["rate"] + proc_config["fixed"]
    sources["processing_fee"] = "deterministic"

    # Returns buffer (percentage of price)
    returns_rate = cat_config.get("returns_rate", 0.07)
    returns_buffer = price * returns_rate
    sources["returns_buffer"] = "estimated"

    # Marketing CAC
    if product.marketing_cac is not None:
        marketing_cac = product.marketing_cac
        sources["marketing_cac"] = "deterministic"
    else:
        cac_range = cat_config.get("typical_cac", (8, 20))
        marketing_cac = sum(cac_range) / 2  # Use midpoint
        sources["marketing_cac"] = "estimated"

    return CostStructure(
        cogs=cogs,
        shipping=shipping,
        packaging=packaging,
        platform_fee=round(platform_fee, 2),
        processing_fee=round(processing_fee, 2),
        returns_buffer=round(returns_buffer, 2),
        marketing_cac=marketing_cac,
        sources=sources,
    )


def compute_unit_economics(product: ProductInput, price: float) -> UnitEconomics:
    """Compute full unit economics at a specific price point.

    This is the central economics calculation. Profit simulations call this
    for every price point to get accurate, fully-loaded profitability.

    Args:
        product: Validated product input.
        price: The selling price.

    Returns:
        UnitEconomics with all margin and profitability metrics.
    """
    costs = compute_cost_structure(product, price)

    all_in_cost = costs.cogs + costs.shipping + costs.packaging
    variable_cost = (
        all_in_cost
        + costs.platform_fee
        + costs.processing_fee
        + costs.returns_buffer
    )
    contribution_margin = price - variable_cost
    contribution_margin_pct = safe_divide(contribution_margin, price)
    break_even_cac = max(0, contribution_margin)
    target_cac = break_even_cac * 0.3  # 30% of margin to acquisition
    profit_after_marketing = contribution_margin - costs.marketing_cac

    return UnitEconomics(
        price=price,
        all_in_cost=round(all_in_cost, 2),
        variable_cost_per_sale=round(variable_cost, 2),
        contribution_margin=round(contribution_margin, 2),
        contribution_margin_pct=round(contribution_margin_pct, 4),
        break_even_cac=round(break_even_cac, 2),
        target_cac=round(target_cac, 2),
        profit_after_marketing=round(profit_after_marketing, 2),
        cost_structure=costs,
    )
