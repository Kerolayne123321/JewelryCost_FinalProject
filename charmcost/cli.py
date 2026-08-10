"""
cli.py

Command-line interface for CharmCost.

Usage:
    python -m charmcost.cli --weight 3.0 --labor 8.00 --margin 50
"""

from __future__ import annotations

import argparse
import sys

from .calculator import METAL_OPTIONS, full_comparison_report
from .spot_price_client import SpotPriceError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare charm material cost & suggested price across metals, using live spot prices."
    )
    parser.add_argument("--weight", type=float, required=True, help="charm weight in grams")
    parser.add_argument("--labor", type=float, default=0.0, help="labor/overhead cost per charm (default: 0)")
    parser.add_argument("--margin", type=float, default=50.0, help="target profit margin as %% of price (default: 50)")
    parser.add_argument(
        "--metals",
        nargs="+",
        choices=list(METAL_OPTIONS.keys()),
        default=None,
        help="which metals to compare (default: 18k_gold 14k_gold sterling_silver)",
    )
    args = parser.parse_args(argv)

    try:
        report = full_comparison_report(
            charm_weight_grams=args.weight,
            labor_cost=args.labor,
            target_margin_pct=args.margin,
            metals=args.metals,
        )
    except (SpotPriceError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    prices = report["spot_prices"]
    print(f"\nSpot prices (as of {prices.get('as_of', 'unknown')}):")
    print(f"  Gold:   ${prices['gold_per_gram_usd']:.4f}/g (24k)")
    print(f"  Silver: ${prices['silver_per_gram_usd']:.4f}/g (fine)")

    print(f"\n{args.weight}g charm, ${args.labor:.2f} labor, {args.margin}% target margin:\n")
    print(f"{'Metal':<26}{'$/g':>10}{'Material':>12}{'Total Cost':>13}{'Suggested Price':>18}{'Profit':>10}")
    for row in report["results"]:
        print(
            f"{row['metal']:<26}"
            f"{row['price_per_gram']:>10.2f}"
            f"{row['material_cost']:>12.2f}"
            f"{row['total_cost']:>13.2f}"
            f"{row['suggested_price']:>18.2f}"
            f"{row['profit_per_charm']:>10.2f}"
        )
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
