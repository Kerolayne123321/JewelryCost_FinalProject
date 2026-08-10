"""
app.py

Flask web interface for CharmCost. Lets a user enter a charm's weight,
labor cost, and target margin, then compares material cost and suggested
retail price across 18k gold, 14k gold, and sterling silver.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from flask import Flask, render_template, request

from charmcost.calculator import DEFAULT_COMPARISON_METALS, METAL_OPTIONS, full_comparison_report
from charmcost.spot_price_client import SpotPriceError

load_dotenv()

app = Flask(__name__)

DEFAULT_WEIGHT = 3.0
DEFAULT_LABOR = 8.0
DEFAULT_MARGIN = 50.0


@app.route("/", methods=["GET", "POST"])
def index():
    form_values = {
        "weight": DEFAULT_WEIGHT,
        "labor": DEFAULT_LABOR,
        "margin": DEFAULT_MARGIN,
        "metals": DEFAULT_COMPARISON_METALS,
    }
    report = None
    error = None

    if request.method == "POST":
        try:
            form_values["weight"] = float(request.form.get("weight", DEFAULT_WEIGHT))
            form_values["labor"] = float(request.form.get("labor", DEFAULT_LABOR))
            form_values["margin"] = float(request.form.get("margin", DEFAULT_MARGIN))
            selected_metals = request.form.getlist("metals") or DEFAULT_COMPARISON_METALS
            form_values["metals"] = selected_metals

            report = full_comparison_report(
                charm_weight_grams=form_values["weight"],
                labor_cost=form_values["labor"],
                target_margin_pct=form_values["margin"],
                metals=selected_metals,
            )
        except ValueError as exc:
            error = str(exc)
        except SpotPriceError as exc:
            error = f"Couldn't reach the live spot price source: {exc}"

    return render_template(
        "index.html",
        metal_options=METAL_OPTIONS,
        form_values=form_values,
        report=report,
        error=error,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
