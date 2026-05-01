"""
Data Quality and Source Reliability Scoring.

Evaluates the quality of input data and tags each output field with its
reliability source. Feeds directly into the confidence score.
"""

from __future__ import annotations
from pricing_engine.models import DataQualityReport, ProductInput, QualityLabel


def assess_data_quality(product: ProductInput) -> DataQualityReport:
    """Assess the quality and reliability of input data."""
    score = 50.0  # Base score
    warnings: list[str] = []
    field_sources: dict[str, str] = {}

    # Product basics are always user-provided
    field_sources["name"] = "deterministic"
    field_sources["category"] = "deterministic"
    field_sources["cost"] = "deterministic"
    field_sources["platform"] = "deterministic"

    # Competitor prices
    n_competitors = len(product.competitor_prices)
    if n_competitors >= 6:
        score += 25
        field_sources["competitor_prices"] = "deterministic"
    elif n_competitors >= 3:
        score += 15
        field_sources["competitor_prices"] = "deterministic"
    elif n_competitors > 0:
        score += 5
        field_sources["competitor_prices"] = "deterministic"
        warnings.append("Limited competitor data. Consider adding more prices for accuracy.")
    else:
        score -= 15
        field_sources["competitor_prices"] = "estimated"
        warnings.append("No competitor data provided. Using category-based market priors.")

    # Shipping
    if product.shipping_cost is not None:
        score += 5
        field_sources["shipping"] = "deterministic"
    else:
        field_sources["shipping"] = "estimated"

    # Packaging
    if product.packaging_cost is not None:
        score += 3
        field_sources["packaging"] = "deterministic"
    else:
        field_sources["packaging"] = "estimated"

    # Marketing CAC
    if product.marketing_cac is not None:
        score += 7
        field_sources["marketing_cac"] = "deterministic"
    else:
        field_sources["marketing_cac"] = "estimated"

    # Target margin
    if product.target_margin is not None:
        score += 3
        field_sources["target_margin"] = "deterministic"
    else:
        field_sources["target_margin"] = "estimated"

    # Positioning
    if product.positioning:
        field_sources["positioning"] = "deterministic"
    else:
        field_sources["positioning"] = "estimated"

    # Elasticity and demand are always heuristic-based
    field_sources["elasticity"] = "estimated"
    field_sources["demand"] = "estimated"

    score = max(0, min(100, score))
    if score >= 70:
        label = QualityLabel.HIGH
    elif score >= 40:
        label = QualityLabel.MEDIUM
    else:
        label = QualityLabel.LOW

    return DataQualityReport(
        score=round(score, 1), label=label,
        field_sources=field_sources, warnings=warnings,
    )
