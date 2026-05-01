"""Edge case tests covering extreme inputs and boundary conditions."""
import pytest
from pricing_engine.models import ProductInput
from pricing_engine.unit_economics import compute_unit_economics
from pricing_engine.market_analysis import analyze_competitors
from pricing_engine.calibration import calibrate
from pricing_engine.ingestion import validate_and_build_input


def test_micro_product():
    """Products below $5 should trigger micro-product handling."""
    product, warnings = validate_and_build_input("Tiny Widget", "general", 2.0)
    assert any("micro-product" in w.lower() for w in warnings)


def test_high_ticket_product():
    """Products above $500 should trigger high-ticket adjustment."""
    product, warnings = validate_and_build_input("Luxury Watch", "luxury", 600.0)
    assert any("high-ticket" in w.lower() for w in warnings)


def test_extreme_margin_capped():
    """Margins > 80% should be capped and warned."""
    product, warnings = validate_and_build_input("Widget", "general", 5.0, target_margin=0.95)
    assert product.target_margin <= 0.80


def test_no_competitor_data():
    """System should work with zero competitors using priors."""
    product = ProductInput(name="New Product", category="electronics", cost=10.0)
    result = analyze_competitors(product)
    assert result.count > 0
    assert result.data_source == "heuristic"


def test_single_competitor():
    """Should function with only 1 competitor price."""
    product = ProductInput(name="Test", category="electronics", cost=10.0, competitor_prices=[25.0])
    result = analyze_competitors(product)
    assert result.median == 25.0


def test_all_same_price():
    """Should handle zero variance in competitor prices."""
    product = ProductInput(name="Test", category="electronics", cost=10.0, competitor_prices=[20, 20, 20, 20])
    result = analyze_competitors(product)
    assert result.std == 0
    assert result.median == 20.0


def test_negative_profit_viability():
    """Costs exceeding price should result in negative margin."""
    product = ProductInput(name="Test", category="electronics", cost=30.0, platform="amazon")
    econ = compute_unit_economics(product, 15.0)
    assert econ.contribution_margin < 0
    assert econ.profit_after_marketing < 0


def test_digital_product_zero_shipping():
    """Digital products should have zero shipping and packaging."""
    product = ProductInput(name="Ebook", category="digital", cost=2.0)
    econ = compute_unit_economics(product, 10.0)
    assert econ.cost_structure.shipping == 0
    assert econ.cost_structure.packaging == 0


def test_extreme_high_margin_calibration_flag():
    """90% margin should be flagged by calibration."""
    product = ProductInput(name="Test", category="electronics", cost=5.0)
    econ = compute_unit_economics(product, 200.0)
    cal = calibrate(product, econ)
    assert not cal.margin_in_range
    assert len(cal.flags) > 0
