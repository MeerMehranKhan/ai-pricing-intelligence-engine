"""
Shared utility functions used across the pricing engine.

Contains helpers for formatting, rounding, safe math operations,
and common data transformations.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero."""
    if denominator == 0:
        return default
    return numerator / denominator


def round_price(price: float) -> float:
    """Round to standard pricing format (2 decimal places)."""
    return round(price, 2)


def apply_charm_pricing(price: float) -> float:
    """Apply psychological charm pricing (.99 ending).

    Rounds to nearest dollar then subtracts 0.01.
    E.g., $30.00 -> $29.99, $45.50 -> $44.99
    """
    rounded = round(price)
    if rounded <= 1:
        return round_price(price)
    return rounded - 0.01


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value to a given range."""
    return max(min_val, min(value, max_val))


def format_currency(value: float) -> str:
    """Format a number as USD currency."""
    if value < 0:
        return f"-${abs(value):,.2f}"
    return f"${value:,.2f}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format a decimal as a percentage string."""
    return f"{value * 100:.{decimals}f}%"


def generate_run_id(product_name: str, timestamp: str) -> str:
    """Generate a deterministic run ID from product name and timestamp."""
    raw = f"{product_name}_{timestamp}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def normalize_category(category: str) -> str:
    """Normalize a user-supplied category string to a config key.

    Handles aliases, case insensitivity, and whitespace.
    """
    from pricing_engine.config import CATEGORY_ALIASES
    cleaned = category.strip().lower().replace("&", "and").replace("_", " ")
    # Direct match
    if cleaned in CATEGORY_ALIASES:
        return CATEGORY_ALIASES[cleaned]
    # Partial match
    for alias, key in CATEGORY_ALIASES.items():
        if alias in cleaned or cleaned in alias:
            return key
    return "general"


def parse_competitor_prices(raw: str | list) -> list[float]:
    """Parse competitor prices from various input formats.

    Supports:
        - List of floats: [19.99, 24.99, 29.99]
        - Comma-separated string: "19.99, 24.99, 29.99"
        - Range string: "19.99-29.99" (generates 3 points)
    """
    if isinstance(raw, list):
        return [float(p) for p in raw if _is_valid_price(p)]

    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return []
        # Range format: "20-50"
        range_match = re.match(r'^(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)$', raw)
        if range_match:
            low, high = float(range_match.group(1)), float(range_match.group(2))
            if low > 0 and high > low:
                mid = (low + high) / 2
                return [low, mid, high]
            return []
        # Comma-separated
        parts = re.split(r'[,;\s]+', raw)
        return [float(p) for p in parts if _is_valid_price(p)]

    return []


def _is_valid_price(val: Any) -> bool:
    """Check if a value can be a valid price."""
    try:
        f = float(val)
        return f > 0
    except (ValueError, TypeError):
        return False


def model_to_dict(model: Any) -> dict:
    """Convert a Pydantic model to a JSON-serializable dict."""
    if hasattr(model, 'model_dump'):
        return json.loads(json.dumps(model.model_dump(), default=str))
    return {}
