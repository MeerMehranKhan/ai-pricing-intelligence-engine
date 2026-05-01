"""Tests for unit economics module."""
import pytest
from pricing_engine.models import ProductInput
from pricing_engine.unit_economics import compute_unit_economics, compute_cost_structure


def _make_product(**kwargs):
    defaults = {"name": "Test", "category": "electronics", "cost": 10.0, "platform": "amazon"}
    defaults.update(kwargs)
    return ProductInput(**defaults)


def test_basic_economics():
    p = _make_product(cost=10.0)
    econ = compute_unit_economics(p, 30.0)
    assert econ.price == 30.0
    assert econ.contribution_margin > 0
    assert econ.contribution_margin_pct > 0
    assert econ.all_in_cost >= 10.0


def test_negative_margin():
    p = _make_product(cost=25.0)
    econ = compute_unit_economics(p, 10.0)
    assert econ.contribution_margin < 0


def test_cost_structure_sources():
    p = _make_product(shipping_cost=5.0)
    cs = compute_cost_structure(p, 30.0)
    assert cs.sources["shipping"] == "deterministic"
    assert cs.sources["cogs"] == "deterministic"


def test_break_even_cac():
    p = _make_product(cost=10.0)
    econ = compute_unit_economics(p, 30.0)
    assert econ.break_even_cac >= 0
    assert econ.target_cac <= econ.break_even_cac


def test_platform_fees_applied():
    p = _make_product(cost=10.0, platform="amazon")
    econ = compute_unit_economics(p, 30.0)
    assert econ.cost_structure.platform_fee > 0


def test_digital_product_no_shipping():
    p = _make_product(cost=2.0, category="digital")
    cs = compute_cost_structure(p, 10.0)
    assert cs.shipping == 0.0
    assert cs.packaging == 0.0
