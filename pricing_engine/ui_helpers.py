"""
Streamlit UI Helper Components.

Contains reusable styled components: metric cards, alert bars,
confidence badges, and custom CSS injection.
"""

from __future__ import annotations
import streamlit as st
from pricing_engine.models import ViabilitySignal, RiskLevel, QualityLabel


def inject_custom_css():
    """Inject premium custom CSS into the Streamlit app."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    .stApp { font-family: 'Inter', sans-serif; }
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid rgba(99,102,241,0.3);
        border-radius: 12px; padding: 20px; margin: 8px 0;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3);
    }
    .metric-card h3 { color: #94a3b8; font-size: 0.85rem; font-weight: 500; margin: 0 0 8px 0; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-card .value { color: #e2e8f0; font-size: 1.8rem; font-weight: 700; margin: 0; }
    .metric-card .subtitle { color: #64748b; font-size: 0.8rem; margin-top: 4px; }
    .top-rec-card {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
        border: 2px solid #6366f1; border-radius: 16px; padding: 24px;
        text-align: center; margin: 16px 0;
    }
    .top-rec-card .price { font-size: 2.5rem; font-weight: 700; color: #a5b4fc; }
    .top-rec-card .label { color: #94a3b8; font-size: 0.9rem; }
    .badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
    .badge-go { background: rgba(34,197,94,0.2); color: #22c55e; border: 1px solid rgba(34,197,94,0.4); }
    .badge-caution { background: rgba(245,158,11,0.2); color: #f59e0b; border: 1px solid rgba(245,158,11,0.4); }
    .badge-nogo { background: rgba(239,68,68,0.2); color: #ef4444; border: 1px solid rgba(239,68,68,0.4); }
    .badge-det { background: rgba(59,130,246,0.2); color: #3b82f6; }
    .badge-est { background: rgba(245,158,11,0.2); color: #f59e0b; }
    .badge-llm { background: rgba(168,85,247,0.2); color: #a855f7; }
    .alert-warning { background: rgba(245,158,11,0.1); border-left: 4px solid #f59e0b; padding: 12px 16px; border-radius: 0 8px 8px 0; margin: 8px 0; color: #fbbf24; }
    .alert-danger { background: rgba(239,68,68,0.1); border-left: 4px solid #ef4444; padding: 12px 16px; border-radius: 0 8px 8px 0; margin: 8px 0; color: #f87171; }
    .alert-info { background: rgba(6,182,212,0.1); border-left: 4px solid #06b6d4; padding: 12px 16px; border-radius: 0 8px 8px 0; margin: 8px 0; color: #67e8f9; }
    .alert-calibration { background: rgba(251,146,60,0.1); border-left: 4px solid #fb923c; padding: 12px 16px; border-radius: 0 8px 8px 0; margin: 8px 0; color: #fdba74; }
    .section-header { color: #a5b4fc; font-size: 1.3rem; font-weight: 600; margin: 24px 0 12px 0; padding-bottom: 8px; border-bottom: 1px solid rgba(99,102,241,0.2); }
    .action-card { background: #1e293b; border-radius: 10px; padding: 16px; margin: 8px 0; border: 1px solid rgba(99,102,241,0.15); }
    .action-card strong { color: #a5b4fc; }
    .limitations { background: rgba(15,23,42,0.8); border: 1px solid rgba(71,85,105,0.3); border-radius: 8px; padding: 16px; margin-top: 24px; color: #64748b; font-size: 0.85rem; }
    </style>
    """, unsafe_allow_html=True)


def render_metric_card(title: str, value: str, subtitle: str = ""):
    """Render a styled metric card."""
    sub_html = f'<p class="subtitle">{subtitle}</p>' if subtitle else ""
    st.markdown(f"""
    <div class="metric-card">
        <h3>{title}</h3>
        <p class="value">{value}</p>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def render_top_recommendation(price: float, signal: ViabilitySignal, strategy: str, confidence: float):
    """Render the top recommendation highlight card."""
    badge_class = {"Go": "badge-go", "Caution": "badge-caution", "No-Go": "badge-nogo"}.get(signal.value, "badge-caution")
    st.markdown(f"""
    <div class="top-rec-card">
        <p class="label">RECOMMENDED PRICE</p>
        <p class="price">${price:,.2f}</p>
        <p><span class="badge {badge_class}">{signal.value}</span></p>
        <p class="label" style="margin-top:8px">{strategy} | Confidence: {confidence:.0f}/100</p>
    </div>
    """, unsafe_allow_html=True)


def render_signal_badge(signal: ViabilitySignal) -> str:
    badge_map = {"Go": "badge-go", "Caution": "badge-caution", "No-Go": "badge-nogo"}
    return f'<span class="badge {badge_map.get(signal.value, "badge-caution")}">{signal.value}</span>'


def render_data_quality_indicator(label: QualityLabel):
    emoji = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}.get(label.value, "🟡")
    st.markdown(f"**Data Quality:** {emoji} {label.value}")


def render_alert(message: str, level: str = "info"):
    """Render a styled alert bar. Levels: info, warning, danger, calibration."""
    st.markdown(f'<div class="alert-{level}">{message}</div>', unsafe_allow_html=True)


def render_source_badge(source: str) -> str:
    badge_map = {"deterministic": "badge-det", "estimated": "badge-est", "llm": "badge-llm"}
    label_map = {"deterministic": "🔵 Deterministic", "estimated": "🟡 Estimated", "llm": "🟣 AI-Generated"}
    cls = badge_map.get(source, "badge-est")
    lbl = label_map.get(source, source)
    return f'<span class="badge {cls}">{lbl}</span>'


def render_limitations():
    """Render the limitations disclosure section."""
    st.markdown("""
    <div class="limitations">
        <strong>Limitations & Disclaimers</strong>
        <ul>
            <li>This analysis uses heuristic models, not real-time market data.</li>
            <li>Demand estimates are directional approximations based on category averages.</li>
            <li>Results should be validated with real-world pricing tests and A/B experiments.</li>
            <li>Competitor data reflects provided inputs, not live market scraping.</li>
            <li>Elasticity uses category priors, not product-specific measured data.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
