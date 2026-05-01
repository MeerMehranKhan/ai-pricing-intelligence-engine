"""
Pydantic data models for the AI Pricing Intelligence Engine.

These models enforce type safety, validation, and serialization across the
entire pipeline. Every module accepts and returns these typed models rather
than raw dicts, ensuring consistency and making the codebase self-documenting.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────────────────────────────

class Positioning(str, Enum):
    BUDGET = "budget"
    MID_TIER = "mid-tier"
    PREMIUM = "premium"


class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class ViabilitySignal(str, Enum):
    GO = "Go"
    CAUTION = "Caution"
    NO_GO = "No-Go"


class SourceTag(str, Enum):
    DETERMINISTIC = "deterministic"
    ESTIMATED = "estimated"
    LLM = "llm"


class QualityLabel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class FragilityLabel(str, Enum):
    ROBUST = "Robust"
    MODERATE = "Moderate"
    FRAGILE = "Fragile"


class ReactionType(str, Enum):
    IGNORE = "Ignore"
    PRICE_MATCH = "Price Matching"
    AGGRESSIVE_UNDERCUT = "Aggressive Undercut"
    FEATURE_COMPETITION = "Feature Competition"


# ──────────────────────────────────────────────────────────────────────────────
# Input Models
# ──────────────────────────────────────────────────────────────────────────────

class ProductInput(BaseModel):
    """All user-provided inputs for a pricing analysis."""
    name: str = Field(..., min_length=1, description="Product name")
    category: str = Field(..., min_length=1, description="Product category")
    cost: float = Field(..., gt=0, description="COGS / product cost in USD")
    market: str = Field(default="United States", description="Target market / region")
    platform: str = Field(default="general", description="Sales platform")
    competitor_prices: list[float] = Field(default_factory=list, description="Known competitor prices")
    positioning: Optional[str] = Field(default=None, description="Desired positioning: budget, mid-tier, premium")
    target_margin: Optional[float] = Field(default=None, ge=0.05, le=0.80, description="Target margin (0.05-0.80)")
    shipping_cost: Optional[float] = Field(default=None, ge=0, description="Override shipping cost")
    packaging_cost: Optional[float] = Field(default=None, ge=0, description="Override packaging cost")
    marketing_cac: Optional[float] = Field(default=None, ge=0, description="Override CAC estimate")
    target_monthly_revenue: Optional[float] = Field(default=None, ge=0, description="Target monthly revenue for scale projection")


# ──────────────────────────────────────────────────────────────────────────────
# Cost & Economics Models
# ──────────────────────────────────────────────────────────────────────────────

class CostStructure(BaseModel):
    """Full cost breakdown for a single unit sale."""
    cogs: float = Field(..., description="Cost of goods sold")
    shipping: float = Field(default=0.0, description="Shipping cost per unit")
    packaging: float = Field(default=0.0, description="Packaging cost per unit")
    platform_fee: float = Field(default=0.0, description="Platform fee per unit (at reference price)")
    processing_fee: float = Field(default=0.0, description="Payment processing fee per unit")
    returns_buffer: float = Field(default=0.0, description="Returns/refund cost buffer per unit")
    marketing_cac: float = Field(default=0.0, description="Customer acquisition cost per unit")
    sources: dict[str, str] = Field(default_factory=dict, description="Source tag per field")


class UnitEconomics(BaseModel):
    """Computed unit economics at a specific price point."""
    price: float
    all_in_cost: float = Field(description="COGS + shipping + packaging")
    variable_cost_per_sale: float = Field(description="All-in cost + fees + returns buffer")
    contribution_margin: float = Field(description="Price - variable cost")
    contribution_margin_pct: float = Field(description="Contribution margin as % of price")
    break_even_cac: float = Field(description="Max affordable CAC")
    target_cac: float = Field(description="Healthy target CAC (30% of margin)")
    profit_after_marketing: float = Field(description="Contribution margin - target CAC")
    cost_structure: CostStructure


# ──────────────────────────────────────────────────────────────────────────────
# Market & Competitor Models
# ──────────────────────────────────────────────────────────────────────────────

class CompetitorAnalysis(BaseModel):
    """Results from analyzing competitor pricing landscape."""
    prices: list[float] = Field(default_factory=list)
    count: int = 0
    mean: float = 0.0
    median: float = 0.0
    std: float = 0.0
    min_price: float = 0.0
    max_price: float = 0.0
    p25: float = 0.0
    p75: float = 0.0
    clusters: list[dict] = Field(default_factory=list, description="Price cluster info")
    segments: dict[str, list[float]] = Field(default_factory=dict, description="Budget/mid/premium segments")
    outliers: list[float] = Field(default_factory=list)
    density_score: float = Field(default=50.0, description="Market crowding 0-100")
    crowding_index: float = Field(default=0.5, description="Overall saturation 0-1")
    gaps: list[dict] = Field(default_factory=list, description="Identified pricing gaps")
    insights: list[str] = Field(default_factory=list, description="Generated insights")
    data_source: str = Field(default="heuristic", description="'user' or 'heuristic'")


class DataQualityReport(BaseModel):
    """Assessment of input data quality and reliability."""
    score: float = Field(default=50.0, ge=0, le=100)
    label: QualityLabel = QualityLabel.MEDIUM
    field_sources: dict[str, str] = Field(default_factory=dict, description="Per-field source tag")
    warnings: list[str] = Field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────────────
# Positioning & Elasticity Models
# ──────────────────────────────────────────────────────────────────────────────

class PositioningResult(BaseModel):
    """Market positioning determination."""
    segment: Positioning = Positioning.MID_TIER
    confidence: float = 0.5
    rationale: str = ""
    alignment_warnings: list[str] = Field(default_factory=list)
    cost_compatible: bool = True
    user_override: bool = False


class ElasticityResult(BaseModel):
    """Price elasticity and demand curve estimation."""
    elasticity_coefficient: float = Field(description="Negative number; |e|>1 = elastic")
    sensitivity_class: str = Field(description="price-sensitive, moderate, or price-resistant")
    demand_base: float = Field(description="Base monthly demand units")
    demand_curve: list[dict] = Field(default_factory=list, description="Price -> demand data points")
    demand_ceiling: float = 0.0
    demand_floor: float = 0.0
    uncertainty_pct: float = 0.15
    assumption_warnings: list[str] = Field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────────────
# Calibration Model
# ──────────────────────────────────────────────────────────────────────────────

class CalibrationResult(BaseModel):
    """Real-world calibration check results."""
    flags: list[str] = Field(default_factory=list)
    margin_in_range: bool = True
    price_in_range: bool = True
    cac_in_range: bool = True
    revenue_realistic: bool = True
    adjustments: dict[str, float] = Field(default_factory=dict)


# ──────────────────────────────────────────────────────────────────────────────
# Strategy Models
# ──────────────────────────────────────────────────────────────────────────────

class StrategyScore(BaseModel):
    """Score and metadata for a single pricing strategy."""
    name: str
    score: float = Field(ge=0, le=100)
    adjusted_price: float = 0.0
    rationale: str = ""


class StrategyResult(BaseModel):
    """Selected pricing strategy with validation."""
    selected: StrategyScore
    alternatives: list[StrategyScore] = Field(default_factory=list)
    validation_status: str = Field(default="Validated", description="Validated / Warning / Overridden")
    fallback: Optional[StrategyScore] = None
    positioning_aligned: bool = True
    all_scores: list[StrategyScore] = Field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────────────
# Simulation Models
# ──────────────────────────────────────────────────────────────────────────────

class ProfitSimulation(BaseModel):
    """Profit simulation across multiple price points."""
    price_points: list[float] = Field(default_factory=list)
    demand: list[float] = Field(default_factory=list)
    revenue: list[float] = Field(default_factory=list)
    total_cost: list[float] = Field(default_factory=list)
    profit: list[float] = Field(default_factory=list)
    max_profit: float = 0.0
    max_profit_price: float = 0.0
    break_even_price: float = 0.0


class ScenarioResult(BaseModel):
    """A single price-change scenario."""
    label: str
    price: float
    demand: float
    revenue: float
    cost: float
    profit: float
    margin_pct: float
    risk_level: str = "Medium"
    when_to_use: str = ""


class ScenarioPlan(BaseModel):
    """Three explicit scenarios: conservative, balanced, aggressive."""
    conservative: ScenarioResult
    balanced: ScenarioResult
    aggressive: ScenarioResult


class TimeProjection(BaseModel):
    """Time-based projection over 90 days."""
    days: list[int] = Field(default_factory=list)
    demand: list[float] = Field(default_factory=list)
    revenue: list[float] = Field(default_factory=list)
    profit: list[float] = Field(default_factory=list)
    cumulative_profit: list[float] = Field(default_factory=list)
    cac: list[float] = Field(default_factory=list)
    phases: list[dict] = Field(default_factory=list)
    break_even_day: Optional[int] = None


# ──────────────────────────────────────────────────────────────────────────────
# Sensitivity & Competitive Reaction Models
# ──────────────────────────────────────────────────────────────────────────────

class SensitivityResult(BaseModel):
    """Business fragility analysis."""
    stability_score: float = Field(ge=0, le=100)
    fragility_label: FragilityLabel = FragilityLabel.MODERATE
    base_profit: float = 0.0
    best_case_profit: float = 0.0
    worst_case_profit: float = 0.0
    variable_impacts: list[dict] = Field(default_factory=list, description="Ranked variable impacts")
    tornado_data: list[dict] = Field(default_factory=list, description="For tornado chart")


class CompetitiveReaction(BaseModel):
    """Predicted competitive response to pricing strategy."""
    reaction_type: ReactionType = ReactionType.IGNORE
    price_war_likelihood: float = Field(default=0.15, ge=0, le=1)
    likelihood_label: str = "Low"
    expected_response: str = ""
    time_horizon: str = ""
    mitigation: str = ""


# ──────────────────────────────────────────────────────────────────────────────
# Risk & Viability Models
# ──────────────────────────────────────────────────────────────────────────────

class RiskAssessment(BaseModel):
    """Composite risk evaluation."""
    level: RiskLevel = RiskLevel.MEDIUM
    score: float = Field(default=50.0, ge=0, le=100)
    primary_reason: str = ""
    contributing_factors: list[str] = Field(default_factory=list)
    mitigation: str = ""


class ViabilityGate(BaseModel):
    """Hard-stop business viability check."""
    passed: bool = True
    signal: ViabilitySignal = ViabilitySignal.GO
    reasons: list[str] = Field(default_factory=list)
    minimum_viable_price: Optional[float] = None


# ──────────────────────────────────────────────────────────────────────────────
# Action & Scale Models
# ──────────────────────────────────────────────────────────────────────────────

class ScaleProjection(BaseModel):
    """Scale feasibility projection."""
    target_revenue: float = 0.0
    required_volume: int = 0
    required_daily_ad_spend: float = 0.0
    total_monthly_marketing: float = 0.0
    feasibility: str = "Achievable"
    constraints: list[str] = Field(default_factory=list)
    break_even_month: Optional[int] = None


class ActionPlan(BaseModel):
    """Actionable next steps derived from analysis."""
    primary_action: str = ""
    target_audience: str = ""
    pricing_tactic: str = ""
    first_test: str = ""
    signal: ViabilitySignal = ViabilitySignal.GO
    platform_actions: list[str] = Field(default_factory=list)
    scale_projection: Optional[ScaleProjection] = None


# ──────────────────────────────────────────────────────────────────────────────
# Final Recommendation Model
# ──────────────────────────────────────────────────────────────────────────────

class PricingRecommendation(BaseModel):
    """Complete pricing recommendation with all supporting analysis."""
    recommended_price: float = 0.0
    min_safe_price: float = 0.0
    max_safe_price: float = 0.0
    contribution_margin: float = 0.0
    contribution_margin_pct: float = 0.0
    profit_estimate: float = 0.0
    confidence_score: float = Field(default=50.0, ge=0, le=100)
    risk: RiskAssessment = Field(default_factory=RiskAssessment)
    viability: ViabilityGate = Field(default_factory=ViabilityGate)
    strategy: Optional[StrategyResult] = None
    explanations: list[str] = Field(default_factory=list)
    source_tags: dict[str, str] = Field(default_factory=dict)


# ──────────────────────────────────────────────────────────────────────────────
# Complete Analysis Run (for storage)
# ──────────────────────────────────────────────────────────────────────────────

class AnalysisRun(BaseModel):
    """A complete, saved pricing analysis."""
    id: Optional[str] = None
    product_input: ProductInput
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1
    unit_economics: Optional[UnitEconomics] = None
    competitor_analysis: Optional[CompetitorAnalysis] = None
    data_quality: Optional[DataQualityReport] = None
    positioning: Optional[PositioningResult] = None
    elasticity: Optional[ElasticityResult] = None
    calibration: Optional[CalibrationResult] = None
    strategy: Optional[StrategyResult] = None
    simulation: Optional[ProfitSimulation] = None
    sensitivity: Optional[SensitivityResult] = None
    time_projection: Optional[TimeProjection] = None
    competitive_reaction: Optional[CompetitiveReaction] = None
    scenario_plan: Optional[ScenarioPlan] = None
    recommendation: Optional[PricingRecommendation] = None
    action_plan: Optional[ActionPlan] = None


class RunComparison(BaseModel):
    """Comparison between two analysis runs."""
    run_a_id: str
    run_b_id: str
    price_delta: float = 0.0
    margin_delta: float = 0.0
    profit_delta: float = 0.0
    risk_delta: float = 0.0
    input_changes: list[str] = Field(default_factory=list)
    impact_summary: str = ""
    better_run: str = ""
