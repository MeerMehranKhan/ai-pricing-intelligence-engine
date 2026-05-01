"""
Plotly Chart Builders.

All charts use a consistent dark-mode friendly color palette and are
designed for responsive Streamlit embedding. Charts are lazy-loaded
(only generated when their section is expanded).
"""

from __future__ import annotations
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pricing_engine.models import (
    CompetitorAnalysis, ElasticityResult, ProfitSimulation,
    ScenarioPlan, SensitivityResult, TimeProjection, UnitEconomics,
)

# Color palette
COLORS = {
    "primary": "#6366f1",    # Indigo
    "secondary": "#8b5cf6",  # Violet
    "success": "#22c55e",    # Green
    "warning": "#f59e0b",    # Amber
    "danger": "#ef4444",     # Red
    "info": "#06b6d4",       # Cyan
    "bg": "#0f172a",         # Slate-900
    "card": "#1e293b",       # Slate-800
    "text": "#e2e8f0",       # Slate-200
    "muted": "#94a3b8",      # Slate-400
    "accent1": "#f472b6",    # Pink
    "accent2": "#34d399",    # Emerald
}

LAYOUT_DEFAULTS = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=COLORS["text"], family="Inter, sans-serif"),
    margin=dict(l=40, r=20, t=40, b=40),
    xaxis=dict(gridcolor="rgba(148,163,184,0.1)", zerolinecolor="rgba(148,163,184,0.2)"),
    yaxis=dict(gridcolor="rgba(148,163,184,0.1)", zerolinecolor="rgba(148,163,184,0.2)"),
)


def profit_vs_price_chart(sim: ProfitSimulation) -> go.Figure:
    """Profit vs price curve with max profit zone highlighted."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=sim.price_points, y=sim.profit, mode="lines",
        name="Profit", line=dict(color=COLORS["primary"], width=3),
        fill="tozeroy", fillcolor="rgba(99,102,241,0.1)",
    ))
    # Max profit marker
    fig.add_trace(go.Scatter(
        x=[sim.max_profit_price], y=[sim.max_profit], mode="markers+text",
        name=f"Max Profit: ${sim.max_profit:,.0f}", text=[f"${sim.max_profit:,.0f}"],
        textposition="top center", marker=dict(size=12, color=COLORS["success"]),
        textfont=dict(color=COLORS["success"]),
    ))
    # Break-even line
    fig.add_vline(x=sim.break_even_price, line_dash="dash", line_color=COLORS["warning"],
                  annotation_text=f"Break-even: ${sim.break_even_price:.2f}")
    fig.update_layout(title="Profit vs. Price", xaxis_title="Price ($)", yaxis_title="Monthly Profit ($)", **LAYOUT_DEFAULTS)
    return fig


def competitor_positioning_chart(comp: CompetitorAnalysis, recommended_price: float) -> go.Figure:
    """Strip chart showing product position relative to competitors."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=comp.prices, y=["Market"] * len(comp.prices), mode="markers",
        name="Competitors", marker=dict(size=12, color=COLORS["muted"], symbol="diamond"),
    ))
    fig.add_trace(go.Scatter(
        x=[comp.median], y=["Market"], mode="markers+text",
        name=f"Median: ${comp.median:.2f}", text=[f"Median ${comp.median:.2f}"],
        textposition="top center", marker=dict(size=16, color=COLORS["warning"], symbol="star"),
    ))
    fig.add_trace(go.Scatter(
        x=[recommended_price], y=["Market"], mode="markers+text",
        name=f"Your Price: ${recommended_price:.2f}", text=[f"Your Price ${recommended_price:.2f}"],
        textposition="bottom center", marker=dict(size=18, color=COLORS["primary"], symbol="circle"),
    ))
    fig.update_layout(title="Competitor Price Positioning", xaxis_title="Price ($)", showlegend=True, height=250, **LAYOUT_DEFAULTS)
    fig.update_yaxes(visible=False)
    return fig


def demand_curve_chart(elasticity: ElasticityResult, recommended_price: float) -> go.Figure:
    """Demand sensitivity curve with uncertainty band."""
    prices = [d["price"] for d in elasticity.demand_curve]
    demands = [d["demand"] for d in elasticity.demand_curve]
    upper = [d * (1 + elasticity.uncertainty_pct) for d in demands]
    lower = [d * (1 - elasticity.uncertainty_pct) for d in demands]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=prices, y=upper, mode="lines", line=dict(width=0), showlegend=False))
    fig.add_trace(go.Scatter(
        x=prices, y=lower, mode="lines", line=dict(width=0),
        fill="tonexty", fillcolor="rgba(99,102,241,0.15)", name="Uncertainty Band",
    ))
    fig.add_trace(go.Scatter(
        x=prices, y=demands, mode="lines", name="Est. Demand",
        line=dict(color=COLORS["secondary"], width=3),
    ))
    fig.add_vline(x=recommended_price, line_dash="dash", line_color=COLORS["success"],
                  annotation_text=f"Rec. Price ${recommended_price:.2f}")
    fig.update_layout(title="Demand Sensitivity Curve", xaxis_title="Price ($)", yaxis_title="Est. Monthly Demand (units)", **LAYOUT_DEFAULTS)
    return fig


def scenario_comparison_chart(scenario_plan: ScenarioPlan) -> go.Figure:
    """Three-scenario comparison: Conservative vs Balanced vs Aggressive."""
    scenarios = [scenario_plan.conservative, scenario_plan.balanced, scenario_plan.aggressive]
    labels = [s.label for s in scenarios]
    colors_map = [COLORS["info"], COLORS["primary"], COLORS["accent1"]]

    fig = make_subplots(rows=1, cols=3, subplot_titles=["Price", "Profit", "Demand"])
    for i, metric in enumerate(["price", "profit", "demand"]):
        values = [getattr(s, metric) for s in scenarios]
        fig.add_trace(go.Bar(
            x=labels, y=values, marker_color=colors_map,
            text=[f"${v:,.0f}" if metric != "demand" else f"{v:,.0f}" for v in values],
            textposition="outside", showlegend=False,
        ), row=1, col=i+1)

    fig.update_layout(title="Scenario Comparison", height=350, **LAYOUT_DEFAULTS)
    return fig


def unit_economics_waterfall(econ: UnitEconomics) -> go.Figure:
    """Cost breakdown waterfall from COGS to final price."""
    cs = econ.cost_structure
    categories = ["COGS", "Shipping", "Packaging", "Platform Fee", "Processing", "Returns Buffer", "Marketing CAC", "Profit"]
    values = [cs.cogs, cs.shipping, cs.packaging, cs.platform_fee, cs.processing_fee, cs.returns_buffer, cs.marketing_cac, econ.profit_after_marketing]
    colors = [COLORS["danger"]] * 7 + [COLORS["success"] if econ.profit_after_marketing > 0 else COLORS["danger"]]

    fig = go.Figure(go.Waterfall(
        x=categories, y=values,
        measure=["relative"]*7 + ["total"],
        connector=dict(line=dict(color=COLORS["muted"], width=1)),
        increasing=dict(marker=dict(color=COLORS["danger"])),
        decreasing=dict(marker=dict(color=COLORS["success"])),
        totals=dict(marker=dict(color=COLORS["primary"])),
        text=[f"${v:.2f}" for v in values], textposition="outside",
    ))
    fig.add_hline(y=econ.price, line_dash="dash", line_color=COLORS["success"],
                  annotation_text=f"Selling Price: ${econ.price:.2f}")
    fig.update_layout(title="Unit Economics Breakdown", yaxis_title="Cost ($)", height=400, **LAYOUT_DEFAULTS)
    return fig


def sensitivity_tornado_chart(tornado_data: list[dict]) -> go.Figure:
    """Tornado chart showing profit sensitivity to each variable."""
    fig = go.Figure()
    variables = [t["variable"] for t in tornado_data]
    base = tornado_data[0]["base"] if tornado_data else 0

    for t in reversed(tornado_data):
        fig.add_trace(go.Bar(
            y=[t["variable"]], x=[t["optimistic"] - base], orientation="h",
            name="Optimistic", marker_color=COLORS["success"], showlegend=False,
            text=[f"${t['optimistic']:,.0f}"], textposition="outside",
        ))
        fig.add_trace(go.Bar(
            y=[t["variable"]], x=[t["pessimistic"] - base], orientation="h",
            name="Pessimistic", marker_color=COLORS["danger"], showlegend=False,
            text=[f"${t['pessimistic']:,.0f}"], textposition="outside",
        ))

    fig.add_vline(x=0, line_color=COLORS["text"], line_width=2)
    fig.update_layout(
        title="Profit Sensitivity (Tornado Chart)", xaxis_title="Profit Change from Base ($)",
        barmode="overlay", height=300, **LAYOUT_DEFAULTS,
    )
    return fig


def time_projection_chart(tp: TimeProjection) -> go.Figure:
    """90-day projection with phase annotations."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(
        x=tp.days, y=tp.revenue, mode="lines", name="Daily Revenue",
        line=dict(color=COLORS["primary"], width=2),
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=tp.days, y=tp.cumulative_profit, mode="lines", name="Cumulative Profit",
        line=dict(color=COLORS["success"], width=2, dash="dot"),
    ), secondary_y=True)
    # Phase annotations
    for phase in tp.phases:
        fig.add_vrect(x0=phase["start"], x1=phase["end"],
                      fillcolor=COLORS["primary"] if phase["phase"] == "Growth" else "rgba(0,0,0,0)",
                      opacity=0.05, line_width=0,
                      annotation_text=phase["phase"], annotation_position="top left")
    if tp.break_even_day:
        fig.add_vline(x=tp.break_even_day, line_dash="dash", line_color=COLORS["warning"],
                      annotation_text=f"Break-even Day {tp.break_even_day}")
    fig.update_layout(title="90-Day Revenue & Profit Projection", xaxis_title="Day", height=400, **LAYOUT_DEFAULTS)
    fig.update_yaxes(title_text="Daily Revenue ($)", secondary_y=False)
    fig.update_yaxes(title_text="Cumulative Profit ($)", secondary_y=True)
    return fig


def competitive_reaction_gauge(likelihood: float) -> go.Figure:
    """Semicircle gauge for price war likelihood."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=likelihood * 100,
        title={"text": "Price War Likelihood", "font": {"color": COLORS["text"]}},
        number={"suffix": "%", "font": {"color": COLORS["text"]}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": COLORS["muted"]},
            "bar": {"color": COLORS["primary"]},
            "bgcolor": COLORS["card"],
            "steps": [
                {"range": [0, 25], "color": "rgba(34,197,94,0.2)"},
                {"range": [25, 50], "color": "rgba(245,158,11,0.2)"},
                {"range": [50, 100], "color": "rgba(239,68,68,0.2)"},
            ],
        },
    ))
    fig.update_layout(height=250, **LAYOUT_DEFAULTS)
    return fig
