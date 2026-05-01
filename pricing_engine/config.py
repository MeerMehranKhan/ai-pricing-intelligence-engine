"""
Configuration module for the AI Pricing Intelligence Engine.

Contains all constants, fee schedules, category benchmarks, elasticity priors,
and platform-specific parameters used throughout the engine. These values are
calibrated against real-world e-commerce data to ensure realistic outputs.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────────────────────────────────────
# LLM Configuration
# ──────────────────────────────────────────────────────────────────────────────

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
USE_LLM = os.getenv("USE_LLM", "false").lower() == "true"

# ──────────────────────────────────────────────────────────────────────────────
# Platform Fee Schedules
# Platform fees are expressed as (percentage_rate, fixed_fee_per_transaction)
# ──────────────────────────────────────────────────────────────────────────────

PLATFORM_FEES: dict[str, dict[str, float]] = {
    "amazon": {"rate": 0.15, "fixed": 0.00, "label": "Amazon (15% referral)"},
    "shopify": {"rate": 0.029, "fixed": 0.30, "label": "Shopify (2.9% + $0.30)"},
    "ebay": {"rate": 0.13, "fixed": 0.30, "label": "eBay (13% + $0.30)"},
    "etsy": {"rate": 0.065, "fixed": 0.20, "label": "Etsy (6.5% + $0.20)"},
    "walmart": {"rate": 0.12, "fixed": 0.00, "label": "Walmart (12%)"},
    "general": {"rate": 0.05, "fixed": 0.00, "label": "General E-commerce (5%)"},
}

# Payment processing fees (applied on top of platform fees)
PAYMENT_PROCESSING_FEES: dict[str, dict[str, float]] = {
    "stripe": {"rate": 0.029, "fixed": 0.30},
    "paypal": {"rate": 0.0349, "fixed": 0.49},
    "default": {"rate": 0.03, "fixed": 0.30},
}

# ──────────────────────────────────────────────────────────────────────────────
# Category Definitions & Elasticity Priors
# Elasticity values are negative (law of demand). Higher absolute value = more
# price-sensitive. These are calibrated against academic research and industry
# reports for typical e-commerce product categories.
# ──────────────────────────────────────────────────────────────────────────────

CATEGORY_CONFIG: dict[str, dict] = {
    "electronics": {
        "elasticity": -1.8,
        "typical_margin": (0.15, 0.30),
        "typical_price_band": (10, 500),
        "returns_rate": 0.08,
        "packaging_cost": 2.50,
        "shipping_weight": "medium",
        "typical_cac": (8, 20),
        "monthly_revenue_norm": 15000,
        "demand_base": 100,
    },
    "beauty": {
        "elasticity": -1.2,
        "typical_margin": (0.60, 0.80),
        "typical_price_band": (5, 80),
        "returns_rate": 0.05,
        "packaging_cost": 1.50,
        "shipping_weight": "light",
        "typical_cac": (10, 25),
        "monthly_revenue_norm": 8000,
        "demand_base": 150,
    },
    "fitness": {
        "elasticity": -1.4,
        "typical_margin": (0.30, 0.55),
        "typical_price_band": (10, 150),
        "returns_rate": 0.06,
        "packaging_cost": 2.00,
        "shipping_weight": "medium",
        "typical_cac": (8, 18),
        "monthly_revenue_norm": 10000,
        "demand_base": 120,
    },
    "food_beverage": {
        "elasticity": -1.0,
        "typical_margin": (0.20, 0.45),
        "typical_price_band": (5, 60),
        "returns_rate": 0.02,
        "packaging_cost": 3.00,
        "shipping_weight": "medium",
        "typical_cac": (5, 15),
        "monthly_revenue_norm": 6000,
        "demand_base": 200,
    },
    "apparel": {
        "elasticity": -1.5,
        "typical_margin": (0.40, 0.65),
        "typical_price_band": (10, 200),
        "returns_rate": 0.15,
        "packaging_cost": 1.00,
        "shipping_weight": "light",
        "typical_cac": (12, 30),
        "monthly_revenue_norm": 12000,
        "demand_base": 130,
    },
    "home_garden": {
        "elasticity": -1.3,
        "typical_margin": (0.35, 0.55),
        "typical_price_band": (8, 200),
        "returns_rate": 0.07,
        "packaging_cost": 3.00,
        "shipping_weight": "heavy",
        "typical_cac": (8, 20),
        "monthly_revenue_norm": 10000,
        "demand_base": 110,
    },
    "luxury": {
        "elasticity": -0.6,
        "typical_margin": (0.55, 0.85),
        "typical_price_band": (50, 2000),
        "returns_rate": 0.04,
        "packaging_cost": 5.00,
        "shipping_weight": "light",
        "typical_cac": (25, 60),
        "monthly_revenue_norm": 20000,
        "demand_base": 40,
    },
    "digital": {
        "elasticity": -2.0,
        "typical_margin": (0.80, 0.95),
        "typical_price_band": (1, 200),
        "returns_rate": 0.02,
        "packaging_cost": 0.00,
        "shipping_weight": "none",
        "typical_cac": (3, 12),
        "monthly_revenue_norm": 8000,
        "demand_base": 250,
    },
    "toys_games": {
        "elasticity": -1.6,
        "typical_margin": (0.30, 0.50),
        "typical_price_band": (5, 100),
        "returns_rate": 0.06,
        "packaging_cost": 2.00,
        "shipping_weight": "medium",
        "typical_cac": (6, 15),
        "monthly_revenue_norm": 8000,
        "demand_base": 140,
    },
    "general": {
        "elasticity": -1.3,
        "typical_margin": (0.25, 0.50),
        "typical_price_band": (5, 300),
        "returns_rate": 0.07,
        "packaging_cost": 2.00,
        "shipping_weight": "medium",
        "typical_cac": (8, 20),
        "monthly_revenue_norm": 10000,
        "demand_base": 120,
    },
}

# Map user-friendly names to internal category keys
CATEGORY_ALIASES: dict[str, str] = {
    "electronics": "electronics",
    "tech": "electronics",
    "gadgets": "electronics",
    "beauty": "beauty",
    "skincare": "beauty",
    "cosmetics": "beauty",
    "fitness": "fitness",
    "sports": "fitness",
    "health": "fitness",
    "food": "food_beverage",
    "food & beverage": "food_beverage",
    "beverage": "food_beverage",
    "apparel": "apparel",
    "clothing": "apparel",
    "fashion": "apparel",
    "home": "home_garden",
    "home & garden": "home_garden",
    "garden": "home_garden",
    "furniture": "home_garden",
    "luxury": "luxury",
    "premium": "luxury",
    "digital": "digital",
    "software": "digital",
    "ebook": "digital",
    "toys": "toys_games",
    "games": "toys_games",
    "toys & games": "toys_games",
    "general": "general",
    "other": "general",
}

# ──────────────────────────────────────────────────────────────────────────────
# Shipping Cost Heuristics
# Costs are in USD, estimated by weight tier and region
# ──────────────────────────────────────────────────────────────────────────────

SHIPPING_COSTS: dict[str, dict[str, float]] = {
    "domestic": {"none": 0.0, "light": 3.50, "medium": 5.50, "heavy": 9.00},
    "international": {"none": 0.0, "light": 8.00, "medium": 14.00, "heavy": 22.00},
}

# ──────────────────────────────────────────────────────────────────────────────
# Market & Region Configuration
# ──────────────────────────────────────────────────────────────────────────────

MARKETS = ["United States", "United Kingdom", "European Union", "Canada", "Australia", "Global"]

# ──────────────────────────────────────────────────────────────────────────────
# Demand Model Parameters
# ──────────────────────────────────────────────────────────────────────────────

DEMAND_CEILING_MULTIPLIER = 3.0      # Max demand = base * 3.0
DEMAND_FLOOR_MULTIPLIER = 0.05       # Min demand = base * 0.05
DIMINISHING_RETURNS_THRESHOLD = 0.5  # Below 50% of market median, diminishing returns kick in

# Uncertainty bands (percentage)
UNCERTAINTY_HIGH_QUALITY = 0.15   # +/- 15% when data quality is High
UNCERTAINTY_MED_QUALITY = 0.22    # +/- 22% when data quality is Medium
UNCERTAINTY_LOW_QUALITY = 0.30    # +/- 30% when data quality is Low

# ──────────────────────────────────────────────────────────────────────────────
# Confidence & Risk Thresholds
# ──────────────────────────────────────────────────────────────────────────────

CONFIDENCE_HIGH = 70
CONFIDENCE_MEDIUM = 40

MARGIN_THIN_THRESHOLD = 0.15      # Below 15% margin = high risk
MARGIN_EXTREME_THRESHOLD = 0.90   # Above 90% = unrealistic

LOW_COST_CUTOFF = 5.0             # Products below $5
HIGH_TICKET_CUTOFF = 500.0        # Products above $500

# ──────────────────────────────────────────────────────────────────────────────
# Platform-specific elasticity adjustments
# Amazon shoppers are more price-sensitive than Shopify DTC buyers
# ──────────────────────────────────────────────────────────────────────────────

PLATFORM_ELASTICITY_MODIFIER: dict[str, float] = {
    "amazon": 1.2,       # 20% more elastic
    "ebay": 1.15,        # 15% more elastic
    "walmart": 1.25,     # 25% more elastic
    "shopify": 0.85,     # 15% less elastic (DTC)
    "etsy": 0.90,        # 10% less elastic (handmade premium)
    "general": 1.0,
}

# ──────────────────────────────────────────────────────────────────────────────
# Positioning multipliers for price recommendations
# ──────────────────────────────────────────────────────────────────────────────

POSITIONING_MULTIPLIERS: dict[str, dict[str, float]] = {
    "budget": {"min": 0.70, "target": 0.85, "max": 0.95},
    "mid-tier": {"min": 0.90, "target": 1.00, "max": 1.15},
    "premium": {"min": 1.10, "target": 1.25, "max": 1.50},
}

# ──────────────────────────────────────────────────────────────────────────────
# Calibration: Revenue-per-SKU norms and sanity caps
# ──────────────────────────────────────────────────────────────────────────────

REVENUE_NORM_MULTIPLIER_CAP = 5.0  # Flag if projected revenue > 5x category norm

# ──────────────────────────────────────────────────────────────────────────────
# Time Projection Parameters
# ──────────────────────────────────────────────────────────────────────────────

TIME_LAUNCH_DAYS = 14
TIME_GROWTH_DAYS = 31    # days 15–45
TIME_STABLE_DAYS = 45    # days 46–90

LAUNCH_DEMAND_FACTOR = 0.35       # 35% of base demand during launch
LAUNCH_CAC_MULTIPLIER = 1.5       # CAC is 50% higher during launch
CONVERSION_IMPROVEMENT = 0.20     # 20% conversion improvement from launch to stable
CAC_OPTIMIZATION_RATE = 0.30      # CAC drops 30% from launch to stable

# ──────────────────────────────────────────────────────────────────────────────
# Sensitivity Analysis Ranges
# ──────────────────────────────────────────────────────────────────────────────

SENSITIVITY_COGS_RANGE = 0.20     # +/- 20%
SENSITIVITY_CAC_RANGE = 0.30      # +/- 30%
SENSITIVITY_DEMAND_RANGE = 0.25   # +/- 25%
SENSITIVITY_FEES_RANGE = 0.10     # +/- 10%
