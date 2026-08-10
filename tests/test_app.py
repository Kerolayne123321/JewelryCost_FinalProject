"""
Smoke tests for the Flask app. Mocks full_comparison_report so no network
calls happen during the test run.
"""

import pytest

import app as app_module


@pytest.fixture
def client():
    app_module.app.config.update(TESTING=True)
    with app_module.app.test_client() as c:
        yield c


FAKE_REPORT = {
    "spot_prices": {
        "gold_per_gram_usd": 139.6403,
        "silver_per_gram_usd": 2.0483,
        "as_of": "2026-08-09T07:34:54.655Z",
        "stale": False,
    },
    "results": [
        {
            "key": "18k_gold", "metal": "18k Gold", "price_per_gram": 104.73,
            "material_cost": 314.19, "total_cost": 322.19,
            "suggested_price": 644.38, "profit_per_charm": 322.19,
        },
    ],
}


def test_index_get_renders_form_with_defaults(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"CharmCost" in response.data
    assert b"3.0" in response.data


def test_index_post_with_valid_input(client, monkeypatch):
    monkeypatch.setattr(app_module, "full_comparison_report", lambda **kwargs: FAKE_REPORT)

    response = client.post("/", data={
        "weight": "3.0", "labor": "8.0", "margin": "50", "metals": "18k_gold",
    })

    assert response.status_code == 200
    assert b"18k Gold" in response.data
    assert b"644.38" in response.data


def test_index_post_with_invalid_weight_shows_error(client):
    response = client.post("/", data={
        "weight": "-1", "labor": "8.0", "margin": "50", "metals": "18k_gold",
    })

    assert response.status_code == 200
    assert b"must be a positive number" in response.data
