"""
Recommendation Engine with Viability Gate.

Assembles all analysis results into a final pricing recommendation.
Includes confidence scoring, composite risk assessment, and hard-stop
business viability checks.
"""

from __future__ import annotations
from pricing_engine.config import POSITIONING_MULTIPLIERS, MARGIN_THIN_THRESHOLD
from pricing_engine.models import (
    CalibrationResult, CompetitorAnalysis, CompetitiveReaction, DataQualityReport,
    ElasticityResult, PositioningResult, PricingRecommendation, ProductInput,
    ProfitSimulation, RiskAssessment, RiskLevel, SensitivityResult,
    StrategyResult, UnitEconomics, ViabilityGate, ViabilitySignal,
)
from pricing_engine.unit_economics import compute_unit_economics
from pricing_engine.utils import safe_divide


def build_recommendation(
    product: ProductInput, unit_economics: UnitEconomics,
    competitor_analysis: CompetitorAnalysis, positioning: PositioningResult,
    elasticity: ElasticityResult, strategy: StrategyResult,
    simulation: ProfitSimulation, data_quality: DataQualityReport,
    calibration: CalibrationResult, sensitivity: SensitivityResult,
    competitive_reaction: CompetitiveReaction,
) -> PricingRecommendation:
    """Build the final pricing recommendation."""
    # Compute recommended price as weighted blend
    profit_max_price = simulation.max_profit_price
    strategy_price = strategy.selected.adjusted_price
    median = competitor_analysis.median if competitor_analysis.median > 0 else product.cost * 2

    # Weights: profit optimization (40%), market fit (30%), strategy (30%)
    recommended = profit_max_price * 0.40 + median * 0.30 + strategy_price * 0.30

    # Apply positioning multiplier
    multipliers = POSITIONING_MULTIPLIERS.get(positioning.segment.value, POSITIONING_MULTIPLIERS["mid-tier"])
    pos_min = median * multipliers["min"]
    pos_max = median * multipliers["max"]
    recommended = max(pos_min, min(pos_max, recommended))

    # Ensure covers costs
    min_viable = product.cost * 1.15
    recommended = max(recommended, min_viable)
    recommended = round(recommended, 2)

    # Safe price range
    min_safe = max(simulation.break_even_price, product.cost * 1.1)
    max_safe = max(recommended * 1.3, competitor_analysis.p75 * 1.1) if competitor_analysis.p75 > 0 else recommended * 1.5

    # Unit economics at recommended price
    rec_econ = compute_unit_economics(product, recommended)

    # Confidence score
    confidence = _compute_confidence(data_quality, competitor_analysis, calibration, positioning)

    # Risk assessment
    risk = _compute_risk(
        rec_econ, competitor_analysis, elasticity, data_quality,
        positioning, sensitivity, competitive_reaction, calibration,
    )

    # Viability gate
    viability = _run_viability_gate(rec_econ, sensitivity, min_viable, product)

    # Source tags
    source_tags = {
        "recommended_price": "estimated",
        "contribution_margin": "deterministic" if data_quality.label.value == "High" else "estimated",
        "profit_estimate": "estimated",
        "confidence_score": "deterministic",
        "risk": "deterministic",
    }

    profit_est = rec_econ.profit_after_marketing * elasticity.demand_base

    return PricingRecommendation(
        recommended_price=recommended,
        min_safe_price=round(min_safe, 2),
        max_safe_price=round(max_safe, 2),
        contribution_margin=rec_econ.contribution_margin,
        contribution_margin_pct=rec_econ.contribution_margin_pct,
        profit_estimate=round(profit_est, 2),
        confidence_score=round(confidence, 1),
        risk=risk, viability=viability,
        strategy=strategy, explanations=[],
        source_tags=source_tags,
    )


def _compute_confidence(
    dq: DataQualityReport, comp: CompetitorAnalysis,
    cal: CalibrationResult, pos: PositioningResult,
) -> float:
    """Compute confidence score (0-100)."""
    score = dq.score * 0.5  # Data quality is 50% of confidence
    if comp.count >= 5:
        score += 20
    elif comp.count >= 3:
        score += 10
    if cal.margin_in_range and cal.price_in_range:
        score += 15
    else:
        score -= 10
    if pos.cost_compatible:
        score += 10
    score += pos.confidence * 5
    return max(0, min(100, score))


def _compute_risk(
    econ: UnitEconomics, comp: CompetitorAnalysis, elast: ElasticityResult,
    dq: DataQualityReport, pos: PositioningResult,
    sens: SensitivityResult, cr: CompetitiveReaction, cal: CalibrationResult,
) -> RiskAssessment:
    """Compute composite risk assessment."""
    risk_score = 0
    factors: list[str] = []
    primary = ""
    mitigation = ""

    # Margin thinness
    if econ.contribution_margin_pct < MARGIN_THIN_THRESHOLD:
        risk_score += 25
        factors.append(f"Thin margins ({econ.contribution_margin_pct*100:.0f}%)")
        if not primary: primary = "Thin margins leave no room for cost increases"
        if not mitigation: mitigation = "Negotiate lower COGS or reduce non-essential costs"

    # Competition density
    if comp.crowding_index > 0.7:
        risk_score += 20
        factors.append("High market competition")
        if not primary: primary = "Crowded market increases price pressure"
        if not mitigation: mitigation = "Differentiate on quality, brand, or service"

    # Demand uncertainty
    if elast.uncertainty_pct > 0.25:
        risk_score += 15
        factors.append("High demand uncertainty")

    # Data quality
    if dq.score < 40:
        risk_score += 15
        factors.append("Low data quality")

    # Positioning mismatch
    if not pos.cost_compatible:
        risk_score += 10
        factors.append("Cost-positioning mismatch")

    # Competitive reaction
    if cr.price_war_likelihood > 0.5:
        risk_score += 15
        factors.append(f"High competitive reaction risk ({cr.likelihood_label})")

    # Sensitivity fragility
    if sens.worst_case_profit < 0:
        risk_score += 15
        factors.append("Negative profit under stress")
        if not primary: primary = "Business model breaks under mild stress"
        if not mitigation: mitigation = "Build cost buffers and test at conservative pricing"

    # Calibration warnings
    if not cal.margin_in_range or not cal.price_in_range:
        risk_score += 5
        factors.append("Outside typical industry ranges")

    risk_score = min(100, risk_score)
    if risk_score >= 60:
        level = RiskLevel.HIGH
    elif risk_score >= 30:
        level = RiskLevel.MEDIUM
    else:
        level = RiskLevel.LOW

    if not primary:
        primary = "No critical risk factors identified"
        mitigation = "Continue with recommended strategy"

    return RiskAssessment(
        level=level, score=risk_score, primary_reason=primary,
        contributing_factors=factors, mitigation=mitigation,
    )


def _run_viability_gate(
    econ: UnitEconomics, sens: SensitivityResult,
    min_viable: float, product: ProductInput,
) -> ViabilityGate:
    """Run hard-stop viability checks."""
    reasons: list[str] = []
    passed = True
    signal = ViabilitySignal.GO

    if econ.profit_after_marketing < 0:
        passed = False
        signal = ViabilitySignal.NO_GO
        reasons.append("Product is not profitable under current assumptions.")

    if econ.contribution_margin_pct < MARGIN_THIN_THRESHOLD:
        if signal != ViabilitySignal.NO_GO:
            signal = ViabilitySignal.CAUTION
        reasons.append(f"Margins are dangerously thin ({econ.contribution_margin_pct*100:.0f}%).")

    if econ.break_even_cac < 2:
        if signal != ViabilitySignal.NO_GO:
            signal = ViabilitySignal.CAUTION
        reasons.append("Not scalable with paid acquisition. Organic-only viable.")

    if sens.worst_case_profit < 0:
        if signal != ViabilitySignal.NO_GO:
            signal = ViabilitySignal.CAUTION
        reasons.append("Business model breaks under mild cost/demand stress.")

    mvp = None
    if not passed:
        # Find minimum viable price
        for mult in [1.5, 1.8, 2.0, 2.5, 3.0]:
            test_price = product.cost * mult
            test_econ = compute_unit_economics(product, test_price)
            if test_econ.profit_after_marketing > 0:
                mvp = round(test_price, 2)
                break

    return ViabilityGate(
        passed=passed, signal=signal, reasons=reasons, minimum_viable_price=mvp,
    )
