"""
Sensitivity Analysis Module.

Tests how fragile the business model is by varying key inputs (COGS, CAC,
demand, fees) and measuring profit impact. Outputs stability score,
fragility label, and tornado chart data.
"""

from __future__ import annotations
from pricing_engine.config import (
    SENSITIVITY_COGS_RANGE, SENSITIVITY_CAC_RANGE,
    SENSITIVITY_DEMAND_RANGE, SENSITIVITY_FEES_RANGE,
)
from pricing_engine.models import FragilityLabel, ProductInput, SensitivityResult, UnitEconomics
from pricing_engine.unit_economics import compute_unit_economics


def run_sensitivity_analysis(
    product: ProductInput, recommended_price: float,
    base_demand: float, base_profit: float,
) -> SensitivityResult:
    """Run sensitivity analysis by varying each input independently."""
    base_econ = compute_unit_economics(product, recommended_price)
    variables = [
        ("COGS", SENSITIVITY_COGS_RANGE, "cost"),
        ("Marketing CAC", SENSITIVITY_CAC_RANGE, "cac"),
        ("Demand", SENSITIVITY_DEMAND_RANGE, "demand"),
        ("Platform Fees", SENSITIVITY_FEES_RANGE, "fees"),
    ]
    tornado_data = []
    all_profits = [base_profit]

    for var_name, var_range, var_type in variables:
        low_profit = _compute_variant_profit(
            product, recommended_price, base_demand, base_econ, var_type, -var_range,
        )
        high_profit = _compute_variant_profit(
            product, recommended_price, base_demand, base_econ, var_type, var_range,
        )
        # For COGS: +COGS = lower profit, -COGS = higher profit
        # For Demand: +Demand = higher profit
        if var_type in ["cost", "cac", "fees"]:
            optimistic, pessimistic = low_profit, high_profit
        else:
            optimistic, pessimistic = high_profit, low_profit

        tornado_data.append({
            "variable": var_name,
            "optimistic": round(optimistic, 2),
            "pessimistic": round(pessimistic, 2),
            "base": round(base_profit, 2),
            "impact": round(abs(optimistic - pessimistic), 2),
        })
        all_profits.extend([optimistic, pessimistic])

    tornado_data.sort(key=lambda x: x["impact"], reverse=True)
    variable_impacts = [{"variable": t["variable"], "impact": t["impact"]} for t in tornado_data]

    best_case = max(all_profits)
    worst_case = min(all_profits)
    profit_range = best_case - worst_case if best_case != worst_case else 1
    stability = max(0, min(100, (1 - (profit_range / max(abs(base_profit), 1))) * 100))

    if stability >= 70:
        fragility = FragilityLabel.ROBUST
    elif stability >= 40:
        fragility = FragilityLabel.MODERATE
    else:
        fragility = FragilityLabel.FRAGILE

    return SensitivityResult(
        stability_score=round(stability, 1), fragility_label=fragility,
        base_profit=round(base_profit, 2), best_case_profit=round(best_case, 2),
        worst_case_profit=round(worst_case, 2),
        variable_impacts=variable_impacts, tornado_data=tornado_data,
    )


def _compute_variant_profit(
    product: ProductInput, price: float, demand: float,
    base_econ: UnitEconomics, var_type: str, delta_pct: float,
) -> float:
    """Compute profit with one variable adjusted by delta_pct."""
    adj_demand = demand
    adj_cost = base_econ.variable_cost_per_sale
    adj_cac = base_econ.cost_structure.marketing_cac

    if var_type == "cost":
        cogs_delta = product.cost * delta_pct
        adj_cost = base_econ.variable_cost_per_sale + cogs_delta
    elif var_type == "cac":
        adj_cac = adj_cac * (1 + delta_pct)
    elif var_type == "demand":
        adj_demand = demand * (1 + delta_pct)
    elif var_type == "fees":
        fee_delta = (base_econ.cost_structure.platform_fee + base_econ.cost_structure.processing_fee) * delta_pct
        adj_cost = base_econ.variable_cost_per_sale + fee_delta

    revenue = price * adj_demand
    total_cost = adj_cost * adj_demand + adj_cac * adj_demand
    return revenue - total_cost
