"""
Data cleaning and normalization module.

Handles cleaning competitor prices, normalizing inputs, removing outliers
from imported data, and preparing data for analysis.
"""

from __future__ import annotations

import numpy as np


def clean_competitor_prices(prices: list[float]) -> list[float]:
    """Clean and validate a list of competitor prices.

    Removes zeros, negatives, and extreme outliers using IQR method.
    """
    if not prices:
        return []

    valid = [p for p in prices if p > 0]
    if len(valid) < 3:
        return valid

    # Remove outliers using IQR
    arr = np.array(valid)
    q1, q3 = np.percentile(arr, [25, 75])
    iqr = q3 - q1

    if iqr == 0:
        return valid

    lower = q1 - 2.5 * iqr
    upper = q3 + 2.5 * iqr

    cleaned = [p for p in valid if lower <= p <= upper]
    return cleaned if cleaned else valid


def normalize_platform(platform: str) -> str:
    """Normalize platform name to a config key."""
    platform = platform.strip().lower()
    platform_map = {
        "amazon": "amazon",
        "amazon.com": "amazon",
        "fba": "amazon",
        "shopify": "shopify",
        "ebay": "ebay",
        "ebay.com": "ebay",
        "etsy": "etsy",
        "etsy.com": "etsy",
        "walmart": "walmart",
        "walmart.com": "walmart",
        "woocommerce": "shopify",
        "bigcommerce": "shopify",
        "general": "general",
        "other": "general",
        "dtc": "shopify",
        "direct": "shopify",
    }
    return platform_map.get(platform, "general")
