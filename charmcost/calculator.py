"""
calculator.py

Business logic: turns live spot prices + a charm's weight into a
material-cost comparison across metal options, and computes a suggested
retail price given labor cost and a target profit margin.
"""

from __future__ import annotations

from .spot_price_client import SpotPriceError, fetch_spot_prices

METAL_OPTIONS = {
    "24k_gold": {"label": "24k Gold", "base": "gold", "purity": 1.0},
    "18k_gold": {"label": "18k Gold", "base": "gold", "purity": 0.75},
    "14k_gold": {"label": "14k Gold", "base": "gold", "purity": 0.5833},
    "10k_gold": {"label": "10k Gold", "base": "gold", "purity": 0.4167},
    "sterling_silver": {"label": "Sterling Silver (.925)", "base": "silver", "purity": 0.925},
    "fine_silver": {"label": "Fine Silver (.999)", "base": "silver", "purity": 0.999},
}

DEFAULT_COMPARISON_METALS = ["18k_gold", "14k_gold", "sterling_silver"]


def compare_metals(charm_weight_grams: float, metals: list[str] | None = None) -> dict:
    if charm_weight_grams <= 0:
        raise ValueError("charm_weight_grams must be a positive number")

    metals = metals or DEFAULT_COMPARISON_METALS
    unknown = [m for m in metals if m not in METAL_OPTIONS]
    if unknown:
        raise ValueError(f"Unknown metal option(s): {unknown}")

    spot_prices = fetch_spot_prices()

    results = []
    for key in metals:
        meta = METAL_OPTIONS[key]
        base_price = (
            spot_prices["gold_per_gram_usd"]
            if meta["base"] == "gold"
            else spot_prices["silver_per_gram_usd"]
        )
        price_per_gram = round(base_price * meta["purity"], 4)
        material_cost = round(price_per_gram * charm_weight_grams, 2)
        results.append({
            "key": key,
            "metal": meta["label"],
            "price_per_gram": price_per_gram,
            "material_cost": material_cost,
        })

    results.sort(key=lambda r: r["material_cost"], reverse=True)

    return {"spot_prices": spot_prices, "results": results}


def suggested_price(material_cost: float, labor_cost: float, target_margin_pct: float) -> dict:
    if material_cost < 0 or labor_cost < 0:
        raise ValueError("material_cost and labor_cost must be non-negative")
    if not 0 <= target_margin_pct < 100:
        raise ValueError("target_margin_pct must be between 0 and 100 (exclusive of 100)")

    total_cost = material_cost + labor_cost
    margin_fraction = target_margin_pct / 100
    price = round(total_cost / (1 - margin_fraction), 2)
    profit = round(price - total_cost, 2)

    return {
        "total_cost": round(total_cost, 2),
        "suggested_price": price,
        "profit_per_charm": profit,
    }


def full_comparison_report(
    charm_weight_grams: float,
    labor_cost: float,
    target_margin_pct: float,
    metals: list[str] | None = None,
) -> dict:
    comparison = compare_metals(charm_weight_grams, metals)

    for row in comparison["results"]:
        pricing = suggested_price(row["material_cost"], labor_cost, target_margin_pct)
        row.update(pricing)

    return comparison
