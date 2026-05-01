"""
Input ingestion and validation for the pricing engine.

Handles parsing user inputs, CSV imports, applying smart defaults,
detecting edge cases, and producing validated ProductInput models.
"""

from __future__ import annotations

import io
from typing import Optional

import pandas as pd

from pricing_engine.config import (
    CATEGORY_CONFIG,
    LOW_COST_CUTOFF,
    HIGH_TICKET_CUTOFF,
    MARGIN_EXTREME_THRESHOLD,
)
from pricing_engine.models import ProductInput
from pricing_engine.utils import normalize_category, parse_competitor_prices


def validate_and_build_input(
    name: str,
    category: str,
    cost: float,
    market: str = "United States",
    platform: str = "general",
    competitor_prices: list[float] | str = "",
    positioning: Optional[str] = None,
    target_margin: Optional[float] = None,
    shipping_cost: Optional[float] = None,
    packaging_cost: Optional[float] = None,
    marketing_cac: Optional[float] = None,
    target_monthly_revenue: Optional[float] = None,
) -> tuple[ProductInput, list[str]]:
    """Validate raw user inputs and return a ProductInput model plus warnings.

    Returns:
        Tuple of (validated ProductInput, list of warning strings).
    """
    warnings: list[str] = []

    # Normalize category
    norm_category = normalize_category(category)

    # Parse competitor prices
    if isinstance(competitor_prices, str):
        prices = parse_competitor_prices(competitor_prices)
    else:
        prices = [p for p in competitor_prices if p > 0]

    # Edge case detection
    if cost < LOW_COST_CUTOFF:
        warnings.append(
            f"This is a micro-product (cost ${cost:.2f} < ${LOW_COST_CUTOFF:.2f}). "
            "Strategies will be adjusted for low-cost items."
        )
    if cost > HIGH_TICKET_CUTOFF:
        warnings.append(
            f"This is a high-ticket product (cost ${cost:.2f} > ${HIGH_TICKET_CUTOFF:.2f}). "
            "Elasticity and strategy will be adjusted."
        )
    if target_margin and target_margin > MARGIN_EXTREME_THRESHOLD:
        warnings.append(
            f"Target margin of {target_margin*100:.0f}% is extremely high. "
            "Margins above 80% are rare outside luxury and digital products."
        )
        target_margin = min(target_margin, 0.80)

    if len(prices) == 0:
        warnings.append(
            "No competitor prices provided. Analysis will use category-based "
            "market priors. Provide at least 3 competitor prices for better accuracy."
        )
    elif len(prices) < 3:
        warnings.append(
            f"Only {len(prices)} competitor price(s) provided. At least 3 are "
            "recommended for reliable market analysis."
        )

    # Validate positioning
    valid_positions = {"budget", "mid-tier", "premium"}
    if positioning and positioning.lower().strip() not in valid_positions:
        warnings.append(
            f"Unknown positioning '{positioning}'. Defaulting to auto-detect."
        )
        positioning = None
    elif positioning:
        positioning = positioning.lower().strip()

    # Normalize platform
    platform = platform.lower().strip()

    product_input = ProductInput(
        name=name.strip(),
        category=norm_category,
        cost=cost,
        market=market,
        platform=platform,
        competitor_prices=prices,
        positioning=positioning,
        target_margin=target_margin,
        shipping_cost=shipping_cost,
        packaging_cost=packaging_cost,
        marketing_cac=marketing_cac,
        target_monthly_revenue=target_monthly_revenue,
    )

    return product_input, warnings


def import_competitor_csv(file_content: bytes | str) -> tuple[list[float], list[str]]:
    """Import competitor prices from a CSV file.

    Auto-detects price columns using fuzzy header matching.

    Returns:
        Tuple of (list of prices, list of warning strings).
    """
    warnings: list[str] = []

    try:
        if isinstance(file_content, bytes):
            df = pd.read_csv(io.BytesIO(file_content))
        else:
            df = pd.read_csv(io.StringIO(file_content))
    except Exception as e:
        return [], [f"Failed to parse CSV: {str(e)}"]

    if df.empty:
        return [], ["CSV file is empty."]

    # Find price column with fuzzy matching
    price_keywords = ["price", "competitor_price", "cost", "amount", "value", "msrp"]
    price_col = None

    for col in df.columns:
        col_lower = col.strip().lower()
        for keyword in price_keywords:
            if keyword in col_lower:
                price_col = col
                break
        if price_col:
            break

    if price_col is None:
        # Try first numeric column
        numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns
        if len(numeric_cols) > 0:
            price_col = numeric_cols[0]
            warnings.append(f"No 'price' column found. Using '{price_col}' as price data.")
        else:
            return [], ["No numeric column found in CSV."]

    prices = pd.to_numeric(df[price_col], errors="coerce").dropna()
    prices = prices[prices > 0].tolist()

    if len(prices) == 0:
        return [], ["No valid prices found in CSV."]

    warnings.append(f"Imported {len(prices)} competitor prices from CSV.")
    return prices, warnings


def import_products_csv(file_content: bytes | str) -> tuple[list[dict], list[str]]:
    """Import product datasets from CSV for batch analysis.

    Returns:
        Tuple of (list of product dicts, list of warnings).
    """
    warnings: list[str] = []

    try:
        if isinstance(file_content, bytes):
            df = pd.read_csv(io.BytesIO(file_content))
        else:
            df = pd.read_csv(io.StringIO(file_content))
    except Exception as e:
        return [], [f"Failed to parse CSV: {str(e)}"]

    if df.empty:
        return [], ["CSV file is empty."]

    # Map columns
    col_map = {}
    required = {"name": ["name", "product", "product_name", "title"],
                 "category": ["category", "type", "product_type"],
                 "cost": ["cost", "cogs", "price", "unit_cost"]}

    for field, keywords in required.items():
        for col in df.columns:
            if col.strip().lower() in keywords:
                col_map[field] = col
                break

    missing = set(required.keys()) - set(col_map.keys())
    if missing:
        return [], [f"Missing required columns: {', '.join(missing)}"]

    products = []
    for _, row in df.iterrows():
        try:
            product = {
                "name": str(row[col_map["name"]]),
                "category": str(row[col_map["category"]]),
                "cost": float(row[col_map["cost"]]),
            }
            products.append(product)
        except (ValueError, TypeError):
            continue

    warnings.append(f"Imported {len(products)} products from CSV.")
    return products, warnings
