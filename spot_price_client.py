"""
spot_price_client.py

Thin client for xaus.com's free, keyless spot price API. Returns live
gold and silver prices in USD per gram of pure metal (24k gold / .999 fine silver).

No API key required. Docs: https://xaus.com/api
"""

from __future__ import annotations

import time

import requests

SPOT_PRICE_URL = "https://xaus.com/api/v1/spot"
REQUEST_TIMEOUT_SECONDS = 15
TROY_OZ_TO_GRAMS = 31.1034768

# Simple in-memory cache so the app doesn't hit the API on every page load /
# keystroke -- this API has no documented hard rate limit but asks for
# "reasonable use," so we cache for a short window.
_CACHE_TTL_SECONDS = 60
_cache: dict = {"prices": None, "fetched_at": 0.0}


class SpotPriceError(Exception):
    """Raised when the spot price API request fails or returns unusable data."""


def fetch_spot_prices(use_cache: bool = True) -> dict:
    """
    Fetch live gold and silver spot prices, in USD per gram of pure metal.

    Returns a dict:
        {
            "gold_per_gram_usd": float,
            "silver_per_gram_usd": float,
            "as_of": str (ISO timestamp from upstream),
            "stale": bool,
        }

    Raises:
        SpotPriceError: if the request fails or the response is missing
        expected fields.
    """
    now = time.monotonic()
    if use_cache and _cache["prices"] and (now - _cache["fetched_at"]) < _CACHE_TTL_SECONDS:
        return _cache["prices"]

    try:
        response = requests.get(SPOT_PRICE_URL, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise SpotPriceError(f"Failed to reach spot price API: {exc}") from exc
    except ValueError as exc:  # invalid JSON
        raise SpotPriceError(f"Failed to parse spot price API response: {exc}") from exc

    try:
        gold_per_gram = float(data["per_gram_usd"])
        silver_per_troy_oz = float(data["silver_usd_oz"])
    except (KeyError, TypeError, ValueError) as exc:
        raise SpotPriceError(f"Spot price API response missing expected fields: {exc}") from exc

    prices = {
        "gold_per_gram_usd": round(gold_per_gram, 4),
        "silver_per_gram_usd": round(silver_per_troy_oz / TROY_OZ_TO_GRAMS, 4),
        "as_of": data.get("price_as_of"),
        "stale": bool(data.get("stale", False)),
    }

    _cache["prices"] = prices
    _cache["fetched_at"] = now
    return prices
