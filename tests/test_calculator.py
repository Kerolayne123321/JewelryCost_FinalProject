"""
Tests for calculator.py. Mocks fetch_spot_prices so no network calls
happen during the test run.
"""

import pytest

from charmcost import calculator

SAMPLE_PRICES = {
    "gold_per_gram_usd": 139.6403,
    "silver_per_gram_usd": 2.0483,
    "as_of": "2026-08-09T07:34:54.655Z",
    "stale": False,
}


@pytest.fixture(autouse=True)
def mock_spot_prices(monkeypatch):
    monkeypatch.setattr(calculator, "fetch_spot_prices", lambda: SAMPLE_PRICES)


def test_compare_metals_default_set_and_ordering():
    result = calculator.compare_metals(charm_weight_grams=3.0)

    labels = [r["metal"] for r in result["results"]]
    assert labels == ["18k Gold", "14k Gold", "Sterling Silver (.925)"]

    eighteen_k = result["results"][0]
    assert eighteen_k["price_per_gram"] == pytest.approx(139.6403 * 0.75, abs=1e-3)
    assert eighteen_k["material_cost"] == pytest.approx(139.6403 * 0.75 * 3.0, abs=1e-2)


def test_compare_metals_custom_metal_list():
    result = calculator.compare_metals(charm_weight_grams=2.0, metals=["24k_gold", "fine_silver"])
    labels = {r["metal"] for r in result["results"]}
    assert labels == {"24k Gold", "Fine Silver (.999)"}


def test_compare_metals_rejects_unknown_metal():
    with pytest.raises(ValueError):
        calculator.compare_metals(charm_weight_grams=2.0, metals=["platinum"])


def test_compare_metals_rejects_non_positive_weight():
    with pytest.raises(ValueError):
        calculator.compare_metals(charm_weight_grams=0)
    with pytest.raises(ValueError):
        calculator.compare_metals(charm_weight_grams=-1.5)


def test_suggested_price_matches_margin_formula():
    result = calculator.suggested_price(material_cost=100.0, labor_cost=20.0, target_margin_pct=50)
    assert result["total_cost"] == 120.0
    assert result["suggested_price"] == 240.0
    assert result["profit_per_charm"] == 120.0


def test_suggested_price_zero_margin_equals_cost():
    result = calculator.suggested_price(material_cost=50.0, labor_cost=10.0, target_margin_pct=0)
    assert result["suggested_price"] == 60.0
    assert result["profit_per_charm"] == 0.0


@pytest.mark.parametrize("bad_margin", [-5, 100, 150])
def test_suggested_price_rejects_invalid_margin(bad_margin):
    with pytest.raises(ValueError):
        calculator.suggested_price(material_cost=50.0, labor_cost=10.0, target_margin_pct=bad_margin)


@pytest.mark.parametrize("material,labor", [(-1, 5), (5, -1)])
def test_suggested_price_rejects_negative_costs(material, labor):
    with pytest.raises(ValueError):
        calculator.suggested_price(material_cost=material, labor_cost=labor, target_margin_pct=50)


def test_full_comparison_report_merges_pricing_into_each_row():
    report = calculator.full_comparison_report(
        charm_weight_grams=3.0, labor_cost=8.0, target_margin_pct=50
    )
    for row in report["results"]:
        assert "suggested_price" in row
        assert "profit_per_charm" in row
        assert row["total_cost"] == pytest.approx(row["material_cost"] + 8.0, abs=1e-2)
