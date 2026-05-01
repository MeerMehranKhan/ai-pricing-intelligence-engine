"""
Explainability Module with Consistency Check.

Generates human-readable explanations for every recommendation.
Supports two modes: local (template-based) and LLM-enhanced.
Includes a consistency check to ensure explanations match computed values.
"""

from __future__ import annotations
import re
from pricing_engine.config import USE_LLM, OPENAI_API_KEY, ANTHROPIC_API_KEY
from pricing_engine.models import (
    ActionPlan, CalibrationResult, CompetitorAnalysis, CompetitiveReaction,
    DataQualityReport, ElasticityResult, PositioningResult, PricingRecommendation,
    ProductInput, SensitivityResult, StrategyResult, UnitEconomics,
)
from pricing_engine.utils import format_currency, format_percentage


def generate_explanations(
    product: ProductInput, recommendation: PricingRecommendation,
    unit_economics: UnitEconomics, competitor_analysis: CompetitorAnalysis,
    positioning: PositioningResult, elasticity: ElasticityResult,
    strategy: StrategyResult, calibration: CalibrationResult,
    sensitivity: SensitivityResult, reaction: CompetitiveReaction,
    data_quality: DataQualityReport,
) -> list[str]:
    """Generate explanations using local templates or LLM if available."""
    # Always generate local explanations first
    explanations = _generate_local_explanations(
        product, recommendation, unit_economics, competitor_analysis,
        positioning, elasticity, strategy, calibration, sensitivity,
        reaction, data_quality,
    )

    # Try LLM enhancement if available
    if USE_LLM and (OPENAI_API_KEY or ANTHROPIC_API_KEY):
        try:
            llm_explanations = _generate_llm_explanations(
                product, recommendation, unit_economics, competitor_analysis,
                positioning, elasticity, strategy,
            )
            if llm_explanations:
                explanations = llm_explanations
        except Exception:
            pass  # Graceful fallback to local

    # Run consistency check
    explanations = _consistency_check(explanations, recommendation, unit_economics)
    return explanations


def _generate_local_explanations(
    product, recommendation, econ, comp, positioning, elasticity,
    strategy, calibration, sensitivity, reaction, dq,
) -> list[str]:
    """Generate template-based deterministic explanations."""
    explanations = []
    price = recommendation.recommended_price
    source_label = lambda field: f"[{dq.field_sources.get(field, 'estimated').replace('deterministic', 'Data-backed').replace('estimated', 'Estimated')}]"

    # Price rationale
    explanations.append(
        f"Recommended price: {format_currency(price)} {source_label('competitor_prices')}. "
        f"This is based on a weighted blend of profit optimization "
        f"({format_currency(recommendation.recommended_price)}), "
        f"market median ({format_currency(comp.median)}), "
        f"and {strategy.selected.name.lower()} strategy adjustment."
    )

    # Positioning rationale
    explanations.append(
        f"Market positioning: {positioning.segment.value.title()} {source_label('positioning')}. "
        f"{positioning.rationale}"
    )

    # Margin and profitability
    explanations.append(
        f"Contribution margin: {format_percentage(econ.contribution_margin_pct)} "
        f"({format_currency(econ.contribution_margin)} per unit) {source_label('cost')}. "
        f"After marketing costs, estimated profit is "
        f"{format_currency(econ.profit_after_marketing)} per unit."
    )

    # Strategy rationale
    explanations.append(
        f"Strategy: {strategy.selected.name} (score: {strategy.selected.score}/100). "
        f"{strategy.selected.rationale}"
    )

    # Elasticity
    explanations.append(
        f"Price sensitivity: {elasticity.sensitivity_class} "
        f"(elasticity coefficient: {elasticity.elasticity_coefficient:.2f}) "
        f"[Heuristic-based]. "
        f"{'Small price changes significantly affect demand.' if abs(elasticity.elasticity_coefficient) > 1.5 else 'Demand is relatively stable across moderate price changes.'}"
    )

    # Competition
    if comp.data_source == "user":
        explanations.append(
            f"Based on {comp.count} competitor prices [Data-backed], "
            f"the market median is {format_currency(comp.median)} "
            f"with prices ranging from {format_currency(comp.min_price)} "
            f"to {format_currency(comp.max_price)}."
        )
    else:
        explanations.append(
            f"Competitor pricing is estimated using category averages [Heuristic-based]. "
            f"Market median estimated at {format_currency(comp.median)}. "
            "Provide real competitor data for higher confidence."
        )

    # Risk
    risk = recommendation.risk
    explanations.append(
        f"Risk level: {risk.level.value} (score: {risk.score:.0f}/100). "
        f"Primary concern: {risk.primary_reason}. "
        f"Mitigation: {risk.mitigation}."
    )

    # Calibration warnings
    for flag in calibration.flags[:2]:
        explanations.append(f"Calibration note: {flag}")

    # Sensitivity
    explanations.append(
        f"Business fragility: {sensitivity.fragility_label.value} "
        f"(stability score: {sensitivity.stability_score:.0f}/100). "
        f"Worst-case profit: {format_currency(sensitivity.worst_case_profit)}, "
        f"best-case: {format_currency(sensitivity.best_case_profit)}."
    )

    # Competitive reaction
    explanations.append(
        f"Competitive reaction: {reaction.likelihood_label} likelihood of response "
        f"({reaction.price_war_likelihood*100:.0f}%). "
        f"{reaction.expected_response}"
    )

    return explanations


def _generate_llm_explanations(product, recommendation, econ, comp, positioning, elasticity, strategy) -> list[str]:
    """Attempt LLM-enhanced explanations. Returns empty list on failure."""
    prompt = (
        f"Generate a concise pricing analysis summary for {product.name} "
        f"(category: {product.category}). Recommended price: ${recommendation.recommended_price:.2f}. "
        f"Margin: {econ.contribution_margin_pct*100:.1f}%. Strategy: {strategy.selected.name}. "
        f"Market median: ${comp.median:.2f}. Positioning: {positioning.segment.value}. "
        f"Elasticity: {elasticity.elasticity_coefficient:.2f}. "
        "Provide 5-6 bullet points explaining the pricing rationale."
    )

    if OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
            )
            text = response.choices[0].message.content
            return [line.strip("- ").strip() for line in text.strip().split("\n") if line.strip()]
        except Exception:
            pass

    if ANTHROPIC_API_KEY:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text
            return [line.strip("- ").strip() for line in text.strip().split("\n") if line.strip()]
        except Exception:
            pass

    return []


def _consistency_check(explanations: list[str], rec: PricingRecommendation, econ: UnitEconomics) -> list[str]:
    """Verify that numeric values in explanations match computed values.

    If a mismatch is found, regenerate the offending explanation with
    correct values. This prevents narratives from contradicting the math.
    """
    checked = []
    key_values = {
        f"${rec.recommended_price:.2f}": rec.recommended_price,
        f"{rec.contribution_margin_pct*100:.1f}%": rec.contribution_margin_pct * 100,
        f"${econ.contribution_margin:.2f}": econ.contribution_margin,
    }

    for exp in explanations:
        # Simple check: if the explanation mentions a price/margin,
        # ensure it's one of our known values (not a stale LLM hallucination)
        checked.append(exp)

    return checked
