"""Tests for simulations module."""
import pytest
from pricing_engine.models import ProductInput, CompetitorAnalysis, ElasticityResult
from pricing_engine.simulations import run_profit_simulation, generate_scenario_plan, generate_time_projection


def _make_inputs():
    product = ProductInput(name="Test", category="electronics", cost=10.0, platform="amazon")
    comp = CompetitorAnalysis(prices=[20,25,30], count=3, median=25, mean=25, min_price=20, max_price=30, p25=22, p75=28)
    elast = ElasticityResult(elasticity_coefficient=-1.5, sensitivity_class="price-sensitive", demand_base=100, demand_ceiling=300, demand_floor=5, uncertainty_pct=0.15)
    return product, comp, elast


def test_simulation_price_points():
    p, c, e = _make_inputs()
    sim = run_profit_simulation(p, e, c)
    assert len(sim.price_points) == 50
    assert len(sim.profit) == 50


def test_max_profit_found():
    p, c, e = _make_inputs()
    sim = run_profit_simulation(p, e, c)
    assert sim.max_profit_price > 0
    assert sim.max_profit == max(sim.profit)


def test_break_even_price():
    p, c, e = _make_inputs()
    sim = run_profit_simulation(p, e, c)
    assert sim.break_even_price > 0


def test_scenario_plan():
    p, c, e = _make_inputs()
    plan = generate_scenario_plan(p, 25, 18, 35, e, c)
    assert plan.conservative.price < plan.balanced.price < plan.aggressive.price


def test_time_projection():
    p, c, e = _make_inputs()
    tp = generate_time_projection(p, 25, e, c)
    assert len(tp.days) == 90
    assert len(tp.revenue) == 90
    assert len(tp.phases) == 3
