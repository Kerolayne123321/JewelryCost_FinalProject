"""CharmCost -- metal cost & margin calculator for charm jewelry, using live gold/silver spot prices."""

from .calculator import compare_metals, full_comparison_report, suggested_price

__all__ = ["compare_metals", "full_comparison_report", "suggested_price"]
__version__ = "0.1.0"
