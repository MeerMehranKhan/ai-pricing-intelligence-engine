"""Tests for market analysis module."""
import pytest
from pricing_engine.models import ProductInput
from pricing_engine.market_analysis import analyze_competitors


def _make_product(**kwargs):
    defaults = {"name": "Test", "category": "electronics", "cost": 10.0}
    defaults.update(kwargs)
    return ProductInput(**defaults)


def test_basic_stats_with_prices():
    p = _make_product(competitor_prices=[10, 20, 30, 40, 50])
    result = analyze_competitors(p)
    assert result.count == 5
    assert result.median == 30.0
    assert result.mean == 30.0
    assert result.min_price == 10.0
    assert result.max_price == 50.0


def test_uses_priors_when_no_prices():
    p = _make_product(competitor_prices=[])
    result = analyze_competitors(p)
    assert result.count > 0
    assert result.data_source == "heuristic"


def test_cluster_detection():
    p = _make_product(competitor_prices=[10, 12, 11, 30, 32, 31, 55, 58, 56])
    result = analyze_competitors(p)
    assert len(result.clusters) >= 2


def test_gap_detection():
    p = _make_product(competitor_prices=[10, 12, 14, 50, 52, 54])
    result = analyze_competitors(p)
    assert len(result.gaps) >= 1
    assert result.gaps[0]["low"] < result.gaps[0]["high"]


def test_density_score_range():
    p = _make_product(competitor_prices=[20, 21, 22, 23, 24])
    result = analyze_competitors(p)
    assert 0 <= result.density_score <= 100


def test_insights_generated():
    p = _make_product(competitor_prices=[15, 16, 17, 18, 19, 20, 45])
    result = analyze_competitors(p)
    assert len(result.insights) > 0
