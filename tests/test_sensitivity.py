"""Tests for sensitivity analysis module."""
import pytest
from pricing_engine.models import ProductInput, FragilityLabel
from pricing_engine.sensitivity_analysis import run_sensitivity_analysis


def test_sensitivity_outputs():
    p = ProductInput(name="Test", category="electronics", cost=10.0, platform="amazon")
    result = run_sensitivity_analysis(p, 25.0, 100.0, 500.0)
    assert 0 <= result.stability_score <= 100
    assert result.fragility_label in [FragilityLabel.ROBUST, FragilityLabel.MODERATE, FragilityLabel.FRAGILE]
    assert result.base_profit == 500.0
    assert result.best_case_profit >= result.base_profit
    assert result.worst_case_profit <= result.base_profit


def test_tornado_data_has_entries():
    p = ProductInput(name="Test", category="electronics", cost=10.0, platform="amazon")
    result = run_sensitivity_analysis(p, 25.0, 100.0, 500.0)
    assert len(result.tornado_data) == 4
    assert all("variable" in t for t in result.tornado_data)
    assert all("impact" in t for t in result.tornado_data)


def test_variable_impacts_ranked():
    p = ProductInput(name="Test", category="electronics", cost=10.0, platform="amazon")
    result = run_sensitivity_analysis(p, 25.0, 100.0, 500.0)
    impacts = [v["impact"] for v in result.variable_impacts]
    assert impacts == sorted(impacts, reverse=True)
