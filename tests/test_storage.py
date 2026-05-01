"""Tests for storage module."""
import os, pytest
from pricing_engine.models import ProductInput, AnalysisRun, PricingRecommendation
from pricing_engine.storage import save_run, load_run, list_runs, delete_run

TEST_DB = "test_pricing.db"

@pytest.fixture(autouse=True)
def cleanup():
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def _make_run():
    return AnalysisRun(product_input=ProductInput(name="TestProduct", category="electronics", cost=10.0), recommendation=PricingRecommendation(recommended_price=25.0))

def test_save_and_load():
    run = _make_run()
    run_id = save_run(run, TEST_DB)
    loaded = load_run(run_id, TEST_DB)
    assert loaded is not None
    assert loaded["product_name"] == "TestProduct"

def test_list_runs():
    save_run(_make_run(), TEST_DB)
    save_run(_make_run(), TEST_DB)
    runs = list_runs(TEST_DB)
    assert len(runs) >= 2

def test_delete_run():
    run_id = save_run(_make_run(), TEST_DB)
    delete_run(run_id, TEST_DB)
    assert load_run(run_id, TEST_DB) is None

def test_version_increments():
    save_run(_make_run(), TEST_DB)
    save_run(_make_run(), TEST_DB)
    runs = list_runs(TEST_DB)
    versions = [r["version"] for r in runs]
    assert max(versions) >= 2
