"""
Profit, Revenue, and Demand Simulations.

Generates profit curves across price points, scenario comparisons,
three-scenario plans, and 90-day time projections.
"""

from __future__ import annotations
import numpy as np
from pricing_engine.config import (
    CATEGORY_CONFIG, TIME_LAUNCH_DAYS, TIME_GROWTH_DAYS, TIME_STABLE_DAYS,
    LAUNCH_DEMAND_FACTOR, LAUNCH_CAC_MULTIPLIER, CAC_OPTIMIZATION_RATE,
)
from pricing_engine.models import (
    CompetitorAnalysis, ElasticityResult, ProductInput, ProfitSimulation,
    ScenarioPlan, ScenarioResult, TimeProjection, UnitEconomics,
)
from pricing_engine.elasticity import compute_demand_at_price
from pricing_engine.unit_economics import compute_unit_economics


def run_profit_simulation(
    product: ProductInput, elasticity: ElasticityResult,
    competitor_analysis: CompetitorAnalysis,
) -> ProfitSimulation:
    """Simulate profit across 50 price points using full unit economics."""
    p_ref = competitor_analysis.median if competitor_analysis.median > 0 else product.cost * 2
    low = max(product.cost * 0.8, p_ref * 0.4)
    high = p_ref * 2.5
    price_points = np.linspace(low, high, 50)

    demands, revenues, costs, profits = [], [], [], []
    max_profit = float("-inf")
    max_profit_price = p_ref
    break_even_price = p_ref

    for price in price_points:
        p = float(price)
        demand = compute_demand_at_price(
            p, p_ref, elasticity.demand_base, elasticity.elasticity_coefficient,
            elasticity.demand_floor, elasticity.demand_ceiling,
        )
        econ = compute_unit_economics(product, p)
        rev = p * demand
        cost = econ.variable_cost_per_sale * demand
        profit = rev - cost - econ.cost_structure.marketing_cac * demand

        demands.append(round(demand, 1))
        revenues.append(round(rev, 2))
        costs.append(round(cost, 2))
        profits.append(round(profit, 2))

        if profit > max_profit:
            max_profit = profit
            max_profit_price = p
        if profit >= 0 and break_even_price == p_ref:
            break_even_price = p

    return ProfitSimulation(
        price_points=[round(float(p), 2) for p in price_points],
        demand=demands, revenue=revenues, total_cost=costs, profit=profits,
        max_profit=round(max_profit, 2), max_profit_price=round(max_profit_price, 2),
        break_even_price=round(break_even_price, 2),
    )


def generate_scenario_plan(
    product: ProductInput, recommended_price: float,
    min_safe: float, max_safe: float,
    elasticity: ElasticityResult, competitor_analysis: CompetitorAnalysis,
) -> ScenarioPlan:
    """Generate conservative, balanced, and aggressive scenarios."""
    p_ref = competitor_analysis.median if competitor_analysis.median > 0 else product.cost * 2

    def build_scenario(label, price, demand_adj, risk, when):
        demand = compute_demand_at_price(
            price, p_ref, elasticity.demand_base, elasticity.elasticity_coefficient,
            elasticity.demand_floor, elasticity.demand_ceiling,
        ) * demand_adj
        econ = compute_unit_economics(product, price)
        rev = price * demand
        cost = econ.variable_cost_per_sale * demand + econ.cost_structure.marketing_cac * demand
        profit = rev - cost
        margin = (price - econ.variable_cost_per_sale) / price if price > 0 else 0
        return ScenarioResult(
            label=label, price=round(price, 2), demand=round(demand, 1),
            revenue=round(rev, 2), cost=round(cost, 2), profit=round(profit, 2),
            margin_pct=round(margin, 4), risk_level=risk, when_to_use=when,
        )

    return ScenarioPlan(
        conservative=build_scenario(
            "Conservative", min_safe * 1.05, 0.85, "Low",
            "Use when entering a crowded market or testing a new category with limited data.",
        ),
        balanced=build_scenario(
            "Balanced", recommended_price, 1.0, "Medium",
            "Use when you have moderate confidence and want a data-driven default.",
        ),
        aggressive=build_scenario(
            "Aggressive", max_safe * 0.95, 1.15, "High",
            "Use when you have a differentiated product with low competition and strong brand.",
        ),
    )


def generate_time_projection(
    product: ProductInput, recommended_price: float,
    elasticity: ElasticityResult, competitor_analysis: CompetitorAnalysis,
) -> TimeProjection:
    """Generate a 90-day time projection with launch/growth/stable phases."""
    p_ref = competitor_analysis.median if competitor_analysis.median > 0 else product.cost * 2
    base_demand = compute_demand_at_price(
        recommended_price, p_ref, elasticity.demand_base,
        elasticity.elasticity_coefficient, elasticity.demand_floor, elasticity.demand_ceiling,
    )
    econ = compute_unit_economics(product, recommended_price)
    daily_base = base_demand / 30
    base_cac = econ.cost_structure.marketing_cac

    days_list, demand_list, revenue_list, profit_list = [], [], [], []
    cumulative_profit_list, cac_list = [], []
    cumulative = 0.0
    phases = [
        {"phase": "Launch", "start": 1, "end": TIME_LAUNCH_DAYS},
        {"phase": "Growth", "start": TIME_LAUNCH_DAYS + 1, "end": TIME_LAUNCH_DAYS + TIME_GROWTH_DAYS},
        {"phase": "Stable", "start": TIME_LAUNCH_DAYS + TIME_GROWTH_DAYS + 1, "end": 90},
    ]
    break_even_day = None

    for day in range(1, 91):
        if day <= TIME_LAUNCH_DAYS:
            demand_factor = LAUNCH_DEMAND_FACTOR + (1 - LAUNCH_DEMAND_FACTOR) * (day / TIME_LAUNCH_DAYS) * 0.3
            cac_factor = LAUNCH_CAC_MULTIPLIER - (LAUNCH_CAC_MULTIPLIER - 1) * (day / TIME_LAUNCH_DAYS) * 0.3
        elif day <= TIME_LAUNCH_DAYS + TIME_GROWTH_DAYS:
            progress = (day - TIME_LAUNCH_DAYS) / TIME_GROWTH_DAYS
            s_curve = 1 / (1 + np.exp(-8 * (progress - 0.5)))
            demand_factor = 0.55 + 0.45 * s_curve
            cac_factor = 1.2 - 0.2 * s_curve
        else:
            demand_factor = 1.0 + np.random.uniform(-0.05, 0.05)
            cac_factor = 1.0

        daily_demand = daily_base * demand_factor
        daily_cac = base_cac * cac_factor
        daily_rev = recommended_price * daily_demand
        daily_cost = econ.variable_cost_per_sale * daily_demand + daily_cac * daily_demand
        daily_profit = daily_rev - daily_cost
        cumulative += daily_profit

        days_list.append(day)
        demand_list.append(round(daily_demand, 2))
        revenue_list.append(round(daily_rev, 2))
        profit_list.append(round(daily_profit, 2))
        cumulative_profit_list.append(round(cumulative, 2))
        cac_list.append(round(daily_cac, 2))

        if break_even_day is None and cumulative > 0:
            break_even_day = day

    return TimeProjection(
        days=days_list, demand=demand_list, revenue=revenue_list,
        profit=profit_list, cumulative_profit=cumulative_profit_list,
        cac=cac_list, phases=phases, break_even_day=break_even_day,
    )
