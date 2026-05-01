"""
Market Analysis Module.

Analyzes competitor pricing landscape including price bands, clustering,
segment detection, outlier identification, market gaps, and crowding metrics.
"""

from __future__ import annotations

import numpy as np

from pricing_engine.config import CATEGORY_CONFIG
from pricing_engine.models import CompetitorAnalysis, ProductInput
from pricing_engine.cleaning import clean_competitor_prices


def _get_category_priors(category: str) -> list[float]:
    """Generate synthetic competitor prices from category priors when no real data is available."""
    cat = CATEGORY_CONFIG.get(category, CATEGORY_CONFIG["general"])
    low, high = cat["typical_price_band"]
    # Generate 8 realistic-looking prices within the category band
    np.random.seed(42)  # Deterministic for reproducibility
    mid = (low + high) / 2
    spread = (high - low) / 4
    prices = np.random.normal(mid, spread, 8)
    prices = np.clip(prices, low, high)
    return sorted([round(float(p), 2) for p in prices])


def analyze_competitors(product: ProductInput) -> CompetitorAnalysis:
    """Perform comprehensive competitor pricing analysis.

    If real competitor prices are provided, uses them directly.
    If not, generates realistic priors from category benchmarks.

    Returns:
        CompetitorAnalysis with statistics, clusters, segments, gaps, and insights.
    """
    # Determine data source
    if product.competitor_prices and len(product.competitor_prices) > 0:
        raw_prices = product.competitor_prices
        data_source = "user"
    else:
        raw_prices = _get_category_priors(product.category)
        data_source = "heuristic"

    prices = clean_competitor_prices(raw_prices)
    if not prices:
        prices = _get_category_priors(product.category)
        data_source = "heuristic"

    arr = np.array(prices)
    count = len(prices)

    # Basic statistics
    mean_price = float(np.mean(arr))
    median_price = float(np.median(arr))
    std_price = float(np.std(arr)) if count > 1 else 0.0
    min_price = float(np.min(arr))
    max_price = float(np.max(arr))
    p25 = float(np.percentile(arr, 25))
    p75 = float(np.percentile(arr, 75))

    # Clustering
    clusters, segments = _cluster_prices(prices)

    # Outlier detection using IQR
    outliers = _detect_outliers(prices)

    # Market density and crowding
    density_score, crowding_index = _compute_density(prices)

    # Gap detection
    gaps = _detect_gaps(prices)

    # Generate insights
    insights = _generate_insights(
        prices, clusters, segments, gaps, outliers, density_score, product
    )

    return CompetitorAnalysis(
        prices=prices,
        count=count,
        mean=round(mean_price, 2),
        median=round(median_price, 2),
        std=round(std_price, 2),
        min_price=round(min_price, 2),
        max_price=round(max_price, 2),
        p25=round(p25, 2),
        p75=round(p75, 2),
        clusters=clusters,
        segments=segments,
        outliers=outliers,
        density_score=round(density_score, 1),
        crowding_index=round(crowding_index, 3),
        gaps=gaps,
        insights=insights,
        data_source=data_source,
    )


def _cluster_prices(prices: list[float]) -> tuple[list[dict], dict[str, list[float]]]:
    """Cluster competitor prices into budget/mid/premium segments.

    Uses KMeans for 6+ prices, simple tercile binning otherwise.
    """
    if len(prices) < 3:
        return [], {"mid-tier": prices}

    sorted_prices = sorted(prices)

    if len(prices) >= 6:
        try:
            from sklearn.cluster import KMeans
            arr = np.array(sorted_prices).reshape(-1, 1)
            n_clusters = min(3, len(prices))
            km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            labels = km.fit_predict(arr)
            centers = km.cluster_centers_.flatten()

            # Sort clusters by center price
            order = np.argsort(centers)
            cluster_names = ["budget", "mid-tier", "premium"]

            clusters = []
            segments: dict[str, list[float]] = {}
            for idx, orig_idx in enumerate(order):
                name = cluster_names[min(idx, 2)]
                cluster_prices = [sorted_prices[i] for i in range(len(sorted_prices)) if labels[i] == orig_idx]
                clusters.append({
                    "segment": name,
                    "center": round(float(centers[orig_idx]), 2),
                    "count": len(cluster_prices),
                    "range": [round(min(cluster_prices), 2), round(max(cluster_prices), 2)],
                })
                segments[name] = cluster_prices

            return clusters, segments
        except ImportError:
            pass

    # Fallback: simple tercile binning
    n = len(sorted_prices)
    t1 = n // 3
    t2 = 2 * n // 3

    segments = {
        "budget": sorted_prices[:t1] if t1 > 0 else [],
        "mid-tier": sorted_prices[t1:t2] if t2 > t1 else sorted_prices,
        "premium": sorted_prices[t2:] if t2 < n else [],
    }

    clusters = []
    for seg_name, seg_prices in segments.items():
        if seg_prices:
            clusters.append({
                "segment": seg_name,
                "center": round(float(np.mean(seg_prices)), 2),
                "count": len(seg_prices),
                "range": [round(min(seg_prices), 2), round(max(seg_prices), 2)],
            })

    return clusters, segments


def _detect_outliers(prices: list[float]) -> list[float]:
    """Detect price outliers using IQR method."""
    if len(prices) < 4:
        return []

    arr = np.array(prices)
    q1, q3 = np.percentile(arr, [25, 75])
    iqr = q3 - q1
    if iqr == 0:
        return []

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return [round(float(p), 2) for p in prices if p < lower or p > upper]


def _compute_density(prices: list[float]) -> tuple[float, float]:
    """Compute market density score (0-100) and crowding index (0-1).

    Density measures how concentrated competitors are in a narrow band.
    Crowding measures overall market saturation.
    """
    if len(prices) < 2:
        return 30.0, 0.3

    arr = np.array(prices)
    cv = float(np.std(arr) / np.mean(arr)) if np.mean(arr) > 0 else 1.0

    # Low CV = tightly clustered = high density
    density_score = max(0, min(100, (1 - cv) * 100))

    # Crowding based on competitor count and density
    count_factor = min(1.0, len(prices) / 10)
    crowding_index = (density_score / 100 * 0.6 + count_factor * 0.4)

    return density_score, crowding_index


def _detect_gaps(prices: list[float]) -> list[dict]:
    """Identify pricing gaps (price ranges with low competitor density)."""
    if len(prices) < 4:
        return []

    sorted_prices = sorted(prices)
    gaps = []

    for i in range(len(sorted_prices) - 1):
        gap_size = sorted_prices[i + 1] - sorted_prices[i]
        avg_price = (sorted_prices[i] + sorted_prices[i + 1]) / 2

        # A gap is significant if it's > 20% of the average price in that range
        if gap_size > avg_price * 0.20:
            gaps.append({
                "low": round(sorted_prices[i], 2),
                "high": round(sorted_prices[i + 1], 2),
                "size": round(gap_size, 2),
                "midpoint": round(avg_price, 2),
            })

    return gaps


def _generate_insights(
    prices: list[float],
    clusters: list[dict],
    segments: dict[str, list[float]],
    gaps: list[dict],
    outliers: list[float],
    density_score: float,
    product: ProductInput,
) -> list[str]:
    """Generate human-readable market insights from analysis results."""
    insights = []

    if len(prices) == 0:
        return ["No competitor data available."]

    median_price = float(np.median(prices))

    # Density insight
    if density_score > 70:
        mid_prices = segments.get("mid-tier", [])
        if mid_prices:
            insights.append(
                f"This market is heavily saturated in the "
                f"${min(mid_prices):.2f}-${max(mid_prices):.2f} band. "
                "Differentiation is critical to compete here."
            )
    elif density_score < 30:
        insights.append(
            "Competitor pricing is widely spread. There may be room for "
            "multiple positioning strategies in this market."
        )

    # Gap insights
    for gap in gaps[:2]:
        insights.append(
            f"There is a pricing gap between ${gap['low']:.2f} and "
            f"${gap['high']:.2f}. This could be an opportunity."
        )

    # Outlier insights
    if outliers:
        low_outliers = [p for p in outliers if p < median_price]
        high_outliers = [p for p in outliers if p > median_price]
        if low_outliers:
            insights.append(
                f"{len(low_outliers)} competitor(s) are priced suspiciously low "
                "compared to the market. These may be loss leaders or low-quality products."
            )
        if high_outliers:
            insights.append(
                f"{len(high_outliers)} competitor(s) are positioned well above "
                "the market. Premium positioning is viable if quality supports it."
            )

    # Position relative to market
    if product.cost > 0:
        min_viable = product.cost * 1.3  # At least 30% markup
        if min_viable > median_price:
            insights.append(
                f"Your minimum viable price (${min_viable:.2f}) is above the "
                f"market median (${median_price:.2f}). You may need premium "
                "positioning or lower COGS to be competitive."
            )

    return insights
