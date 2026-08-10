"""
Tests for spot_price_client.py. Network calls are mocked so these run
offline and aren't flaky due to live market data or external API downtime.
"""

import pytest
import requests

from charmcost import spot_price_client


class FakeResponse:
    def __init__(self, json_data: dict, status_code: int = 200):
        self._json_data = json_data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")

    def json(self):
        return self._json_data


SAMPLE_RESPONSE = {
    "per_gram_usd": 139.6403,
    "silver_usd_oz": 63.707001,
    "price_as_of": "2026-08-09T07:34:54.655Z",
    "stale": False,
}


@pytest.fixture(autouse=True)
def clear_cache():
    """Reset the module-level cache before every test so tests don't leak state."""
    spot_price_client._cache["prices"] = None
    spot_price_client._cache["fetched_at"] = 0.0
    yield


def test_fetch_spot_prices_converts_silver_to_per_gram(monkeypatch):
    monkeypatch.setattr(
        spot_price_client.requests, "get", lambda *a, **k: FakeResponse(SAMPLE_RESPONSE)
    )

    prices = spot_price_client.fetch_spot_prices(use_cache=False)

    assert prices["gold_per_gram_usd"] == pytest.approx(139.6403)
    # 63.707001 / 31.1034768 ≈ 2.0483
    assert prices["silver_per_gram_usd"] == pytest.approx(2.0483, abs=1e-3)
    assert prices["stale"] is False


def test_fetch_spot_prices_uses_cache_within_ttl(monkeypatch):
    call_count = {"n": 0}

    def fake_get(*args, **kwargs):
        call_count["n"] += 1
        return FakeResponse(SAMPLE_RESPONSE)

    monkeypatch.setattr(spot_price_client.requests, "get", fake_get)

    first = spot_price_client.fetch_spot_prices(use_cache=True)
    second = spot_price_client.fetch_spot_prices(use_cache=True)

    assert call_count["n"] == 1
    assert first == second


def test_fetch_spot_prices_bypasses_cache_when_disabled(monkeypatch):
    call_count = {"n": 0}

    def fake_get(*args, **kwargs):
        call_count["n"] += 1
        return FakeResponse(SAMPLE_RESPONSE)

    monkeypatch.setattr(spot_price_client.requests, "get", fake_get)

    spot_price_client.fetch_spot_prices(use_cache=False)
    spot_price_client.fetch_spot_prices(use_cache=False)

    assert call_count["n"] == 2


def test_fetch_spot_prices_wraps_network_errors(monkeypatch):
    def raise_connection_error(*args, **kwargs):
        raise requests.ConnectionError("network down")

    monkeypatch.setattr(spot_price_client.requests, "get", raise_connection_error)

    with pytest.raises(spot_price_client.SpotPriceError):
        spot_price_client.fetch_spot_prices(use_cache=False)


def test_fetch_spot_prices_raises_on_missing_fields(monkeypatch):
    monkeypatch.setattr(
        spot_price_client.requests, "get", lambda *a, **k: FakeResponse({"unexpected": "shape"})
    )

    with pytest.raises(spot_price_client.SpotPriceError):
        spot_price_client.fetch_spot_prices(use_cache=False)


def test_fetch_spot_prices_raises_on_http_error(monkeypatch):
    monkeypatch.setattr(
        spot_price_client.requests, "get", lambda *a, **k: FakeResponse({}, status_code=500)
    )

    with pytest.raises(spot_price_client.SpotPriceError):
        spot_price_client.fetch_spot_prices(use_cache=False)
