"""
AI Pricing Intelligence Engine — Main Streamlit Application.

This is the entry point. Run with: streamlit run app.py
"""

from __future__ import annotations
import json
import time
import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="AI Pricing Intelligence Engine",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

from pricing_engine.config import CATEGORY_CONFIG, MARKETS, PLATFORM_FEES, USE_LLM
from pricing_engine.models import AnalysisRun, QualityLabel, ViabilitySignal
from pricing_engine.ingestion import validate_and_build_input, import_competitor_csv
from pricing_engine.cleaning import normalize_platform
from pricing_engine.unit_economics import compute_unit_economics
from pricing_engine.market_analysis import analyze_competitors
from pricing_engine.positioning import determine_positioning
from pricing_engine.elasticity import estimate_elasticity, compute_demand_at_price
from pricing_engine.calibration import calibrate
from pricing_engine.pricing_strategy import select_strategy
from pricing_engine.simulations import run_profit_simulation, generate_scenario_plan, generate_time_projection
from pricing_engine.sensitivity_analysis import run_sensitivity_analysis
from pricing_engine.competitive_reaction import predict_competitive_reaction
from pricing_engine.data_quality import assess_data_quality
from pricing_engine.recommendations import build_recommendation
from pricing_engine.actions import generate_action_plan
from pricing_engine.explanations import generate_explanations
from pricing_engine.storage import save_run, list_runs, load_run, delete_run, compare_runs
from pricing_engine.reporting import export_json_bytes, export_csv_bytes, export_pdf_bytes
from pricing_engine.charts import (
    profit_vs_price_chart, competitor_positioning_chart, demand_curve_chart,
    scenario_comparison_chart, unit_economics_waterfall, sensitivity_tornado_chart,
    time_projection_chart, competitive_reaction_gauge,
)
from pricing_engine.ui_helpers import (
    inject_custom_css, render_metric_card, render_top_recommendation,
    render_data_quality_indicator, render_alert, render_limitations,
    render_source_badge,
)
from pricing_engine.utils import format_currency, format_percentage, model_to_dict


def main():
    inject_custom_css()

    # ── Sidebar ──
    with st.sidebar:
        st.markdown("## 💰 Pricing Engine")
        st.markdown("---")

        # Demo mode
        demo_mode = st.toggle("🎮 Demo Mode", value=False, help="Load sample products for exploration")

        # CSV Import
        st.markdown("### 📤 Import Data")
        uploaded_csv = st.file_uploader("Upload competitor CSV", type=["csv"], help="CSV with a 'price' column")
        imported_prices: list[float] = []
        if uploaded_csv:
            prices, warnings = import_competitor_csv(uploaded_csv.read())
            imported_prices = prices
            for w in warnings:
                st.info(w)

        # History
        st.markdown("### 📜 History")
        runs = list_runs()
        if runs:
            for run_info in runs[:10]:
                col1, col2 = st.columns([3, 1])
                with col1:
                    if st.button(f"📊 {run_info['product_name']} v{run_info['version']}", key=f"load_{run_info['id']}"):
                        st.session_state["loaded_run"] = load_run(run_info["id"])
                with col2:
                    if st.button("🗑️", key=f"del_{run_info['id']}"):
                        delete_run(run_info["id"])
                        st.rerun()
        else:
            st.caption("No saved analyses yet.")

        # Mode indicator
        st.markdown("---")
        mode = "🤖 AI-Enhanced" if USE_LLM else "📊 Local Mode"
        st.caption(f"Engine: {mode}")

    # ── Main Area ──
    st.markdown("# 💰 AI Pricing Intelligence Engine")
    st.markdown("*Decision-grade pricing analysis for e-commerce products*")

    # Load sample data if demo mode
    sample_products = []
    if demo_mode:
        with open("data/sample_products.json") as f:
            sample_products = json.load(f)

    # ── Input Section ──
    st.markdown('<p class="section-header">📋 Product Details</p>', unsafe_allow_html=True)

    if demo_mode and sample_products:
        selected_demo = st.selectbox(
            "Select a demo product",
            [p["name"] for p in sample_products],
            help="Pre-filled with realistic data for exploration",
        )
        demo_product = next(p for p in sample_products if p["name"] == selected_demo)
    else:
        demo_product = None

    col1, col2 = st.columns(2)
    with col1:
        product_name = st.text_input("Product Name", value=demo_product["name"] if demo_product else "", help="What are you selling?")
        categories = list(CATEGORY_CONFIG.keys())
        cat_idx = categories.index(demo_product["category"]) if demo_product and demo_product["category"] in categories else 0
        category = st.selectbox("Category", categories, index=cat_idx, format_func=lambda x: x.replace("_", " ").title())
        cost = st.number_input("Product Cost (COGS) $", min_value=0.01, value=float(demo_product["cost"]) if demo_product else 10.0, step=0.50, help="Your cost to acquire/manufacture one unit")
    with col2:
        market = st.selectbox("Target Market", MARKETS, index=0)
        platforms = list(PLATFORM_FEES.keys())
        plat_idx = platforms.index(demo_product["platform"]) if demo_product and demo_product.get("platform") in platforms else 0
        platform = st.selectbox("Platform", platforms, index=plat_idx, format_func=lambda x: PLATFORM_FEES[x]["label"])

        comp_default = ", ".join(str(p) for p in demo_product["competitor_prices"]) if demo_product else ""
        if imported_prices:
            comp_default = ", ".join(str(p) for p in imported_prices)
        competitor_input = st.text_area("Competitor Prices (comma-separated)", value=comp_default, help="Enter known competitor prices. At least 3 recommended.", height=68)

    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        adv1, adv2, adv3 = st.columns(3)
        with adv1:
            positioning = st.selectbox("Positioning Preference", ["Auto-detect", "Budget", "Mid-tier", "Premium"], index=0)
            positioning = None if positioning == "Auto-detect" else positioning.lower()
            target_margin = st.slider("Target Margin %", 5, 80, value=int(demo_product["target_margin"]*100) if demo_product and demo_product.get("target_margin") else 40, step=5, help="Desired profit margin percentage") / 100
        with adv2:
            shipping = st.number_input("Shipping Cost $", min_value=0.0, value=float(demo_product.get("shipping_cost", 0)) if demo_product else 0.0, step=0.50)
            packaging = st.number_input("Packaging Cost $", min_value=0.0, value=float(demo_product.get("packaging_cost", 0)) if demo_product else 0.0, step=0.50)
        with adv3:
            marketing_cac = st.number_input("Marketing CAC $", min_value=0.0, value=float(demo_product.get("marketing_cac", 0)) if demo_product else 0.0, step=1.0, help="Cost to acquire one customer")
            scale_target = st.number_input("Target Monthly Revenue $", min_value=0.0, value=0.0, step=1000.0, help="For 'Scale This Business' projection")

    # ── Run Analysis ──
    if st.button("🚀 Run Pricing Analysis", type="primary", use_container_width=True):
        if not product_name or cost <= 0:
            st.error("Please enter a product name and valid cost.")
            return

        progress = st.progress(0)
        status = st.empty()

        # Step 1: Validate inputs
        status.text("⏳ Validating inputs...")
        progress.progress(5)
        product_input, input_warnings = validate_and_build_input(
            name=product_name, category=category, cost=cost, market=market,
            platform=normalize_platform(platform), competitor_prices=competitor_input,
            positioning=positioning, target_margin=target_margin,
            shipping_cost=shipping if shipping > 0 else None,
            packaging_cost=packaging if packaging > 0 else None,
            marketing_cac=marketing_cac if marketing_cac > 0 else None,
            target_monthly_revenue=scale_target if scale_target > 0 else None,
        )
        for w in input_warnings:
            render_alert(w, "warning")

        # Step 2: Data quality
        status.text("⏳ Assessing data quality...")
        progress.progress(10)
        data_quality = assess_data_quality(product_input)

        # Step 3: Market analysis
        status.text("⏳ Analyzing market conditions...")
        progress.progress(20)
        competitor_analysis = analyze_competitors(product_input)

        # Step 4: Unit economics
        status.text("⏳ Computing unit economics...")
        progress.progress(30)
        ref_price = competitor_analysis.median if competitor_analysis.median > 0 else cost * 2
        unit_econ = compute_unit_economics(product_input, ref_price)

        # Step 5: Positioning
        status.text("⏳ Determining market positioning...")
        progress.progress(35)
        positioning_result = determine_positioning(product_input, competitor_analysis, unit_econ)

        # Step 6: Elasticity
        status.text("⏳ Estimating demand sensitivity...")
        progress.progress(45)
        elasticity = estimate_elasticity(product_input, competitor_analysis, positioning_result, data_quality.label)

        # Step 7: Calibration
        status.text("⏳ Calibrating against benchmarks...")
        progress.progress(50)
        monthly_rev = ref_price * elasticity.demand_base
        calibration = calibrate(product_input, unit_econ, monthly_rev)

        # Step 8: Strategy
        status.text("⏳ Evaluating pricing strategies...")
        progress.progress(60)
        strategy = select_strategy(product_input, competitor_analysis, positioning_result, elasticity, unit_econ)

        # Step 9: Simulations
        status.text("⏳ Running profit simulations...")
        progress.progress(70)
        simulation = run_profit_simulation(product_input, elasticity, competitor_analysis)

        # Step 10: Sensitivity
        status.text("⏳ Testing business fragility...")
        progress.progress(75)
        base_demand = compute_demand_at_price(
            strategy.selected.adjusted_price,
            competitor_analysis.median if competitor_analysis.median > 0 else cost * 2,
            elasticity.demand_base, elasticity.elasticity_coefficient,
            elasticity.demand_floor, elasticity.demand_ceiling,
        )
        base_profit_est = simulation.max_profit
        sensitivity = run_sensitivity_analysis(product_input, strategy.selected.adjusted_price, base_demand, base_profit_est)

        # Step 11: Competitive reaction
        status.text("⏳ Modeling competitive reactions...")
        progress.progress(80)
        reaction = predict_competitive_reaction(strategy, competitor_analysis, positioning_result, strategy.selected.adjusted_price)

        # Step 12: Recommendation
        status.text("⏳ Generating recommendations...")
        progress.progress(85)
        recommendation = build_recommendation(
            product_input, unit_econ, competitor_analysis, positioning_result,
            elasticity, strategy, simulation, data_quality, calibration,
            sensitivity, reaction,
        )

        # Step 13: Scenarios & time projection
        status.text("⏳ Building scenario plans...")
        progress.progress(88)
        scenario_plan = generate_scenario_plan(
            product_input, recommendation.recommended_price,
            recommendation.min_safe_price, recommendation.max_safe_price,
            elasticity, competitor_analysis,
        )
        time_proj = generate_time_projection(product_input, recommendation.recommended_price, elasticity, competitor_analysis)

        # Step 14: Action plan
        status.text("⏳ Creating action plan...")
        progress.progress(90)
        rec_econ = compute_unit_economics(product_input, recommendation.recommended_price)
        action_plan = generate_action_plan(product_input, recommendation, rec_econ, strategy, competitor_analysis, elasticity)

        # Step 15: Explanations
        status.text("⏳ Generating explanations...")
        progress.progress(95)
        explanations = generate_explanations(
            product_input, recommendation, rec_econ, competitor_analysis,
            positioning_result, elasticity, strategy, calibration,
            sensitivity, reaction, data_quality,
        )
        recommendation.explanations = explanations

        progress.progress(100)
        status.text("✅ Analysis complete!")
        time.sleep(0.5)
        progress.empty()
        status.empty()

        # Store results in session state
        run = AnalysisRun(
            product_input=product_input, unit_economics=rec_econ,
            competitor_analysis=competitor_analysis, data_quality=data_quality,
            positioning=positioning_result, elasticity=elasticity,
            calibration=calibration, strategy=strategy, simulation=simulation,
            sensitivity=sensitivity, time_projection=time_proj,
            competitive_reaction=reaction, scenario_plan=scenario_plan,
            recommendation=recommendation, action_plan=action_plan,
        )
        st.session_state["current_run"] = run
        st.session_state["run_data"] = model_to_dict(run)

    # ── Results Display ──
    if "current_run" in st.session_state:
        run: AnalysisRun = st.session_state["current_run"]
        run_data = st.session_state["run_data"]
        rec = run.recommendation
        strat = run.strategy
        dq = run.data_quality

        # Data quality indicator
        render_data_quality_indicator(dq.label)

        # Calibration warnings
        if run.calibration and run.calibration.flags:
            for flag in run.calibration.flags:
                render_alert(flag, "calibration")

        # Viability gate warnings
        if rec.viability.signal == ViabilitySignal.NO_GO:
            for reason in rec.viability.reasons:
                render_alert(f"⛔ {reason}", "danger")
            if rec.viability.minimum_viable_price:
                render_alert(f"Minimum viable price: {format_currency(rec.viability.minimum_viable_price)}", "warning")
        elif rec.viability.signal == ViabilitySignal.CAUTION:
            for reason in rec.viability.reasons:
                render_alert(f"⚠️ {reason}", "warning")

        # Top recommendation
        render_top_recommendation(
            rec.recommended_price, rec.viability.signal,
            strat.selected.name, rec.confidence_score,
        )

        # Metric cards row
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            render_metric_card("Safe Range", f"{format_currency(rec.min_safe_price)} - {format_currency(rec.max_safe_price)}", "Min - Max")
        with m2:
            render_metric_card("Margin", format_percentage(rec.contribution_margin_pct), f"{format_currency(rec.contribution_margin)} / unit")
        with m3:
            render_metric_card("Est. Monthly Profit", format_currency(rec.profit_estimate), "At base demand")
        with m4:
            render_metric_card("Confidence", f"{rec.confidence_score:.0f}/100", dq.label.value + " data quality")
        with m5:
            render_metric_card("Risk", rec.risk.level.value, rec.risk.primary_reason[:40])

        st.markdown("---")

        # Tabs for detailed sections
        tabs = st.tabs(["📊 Profit Simulation", "🏪 Competitors", "📈 Demand", "🎯 Strategy",
                        "📋 Scenarios", "⏱️ Timeline", "🛡️ Fragility", "⚔️ Competition", "🚀 Action Plan", "📝 Explanations"])

        with tabs[0]:
            st.plotly_chart(profit_vs_price_chart(run.simulation), use_container_width=True)
            st.plotly_chart(unit_economics_waterfall(run.unit_economics), use_container_width=True)

        with tabs[1]:
            st.plotly_chart(competitor_positioning_chart(run.competitor_analysis, rec.recommended_price), use_container_width=True)
            if run.competitor_analysis.insights:
                for insight in run.competitor_analysis.insights:
                    render_alert(insight, "info")

        with tabs[2]:
            st.plotly_chart(demand_curve_chart(run.elasticity, rec.recommended_price), use_container_width=True)
            st.caption(f"Elasticity: {run.elasticity.elasticity_coefficient:.2f} ({run.elasticity.sensitivity_class})")
            for w in run.elasticity.assumption_warnings:
                st.caption(f"⚠️ {w}")

        with tabs[3]:
            st.markdown(f"### Recommended: **{strat.selected.name}** (Score: {strat.selected.score:.0f}/100)")
            st.markdown(strat.selected.rationale)
            if strat.validation_status != "Validated":
                render_alert(f"Strategy validation: {strat.validation_status}", "warning")
            st.markdown("#### All Strategies Ranked")
            for s in strat.all_scores:
                bar_pct = s.score
                st.markdown(f"**{s.name}**: {s.score:.0f}/100 | ${s.adjusted_price:.2f}")
                st.progress(int(min(bar_pct, 100)))

        with tabs[4]:
            st.plotly_chart(scenario_comparison_chart(run.scenario_plan), use_container_width=True)
            sc1, sc2, sc3 = st.columns(3)
            for col, scenario in zip([sc1, sc2, sc3], [run.scenario_plan.conservative, run.scenario_plan.balanced, run.scenario_plan.aggressive]):
                with col:
                    render_metric_card(scenario.label, format_currency(scenario.price), f"Profit: {format_currency(scenario.profit)}")
                    st.caption(f"Risk: {scenario.risk_level}")
                    st.caption(scenario.when_to_use)

        with tabs[5]:
            st.plotly_chart(time_projection_chart(run.time_projection), use_container_width=True)
            if run.time_projection.break_even_day:
                st.success(f"📅 Estimated break-even: Day {run.time_projection.break_even_day}")

        with tabs[6]:
            st.plotly_chart(sensitivity_tornado_chart(run.sensitivity.tornado_data), use_container_width=True)
            s1, s2, s3 = st.columns(3)
            with s1: render_metric_card("Stability", f"{run.sensitivity.stability_score:.0f}/100", run.sensitivity.fragility_label.value)
            with s2: render_metric_card("Best Case", format_currency(run.sensitivity.best_case_profit), "All variables favorable")
            with s3: render_metric_card("Worst Case", format_currency(run.sensitivity.worst_case_profit), "All variables unfavorable")

        with tabs[7]:
            st.plotly_chart(competitive_reaction_gauge(run.competitive_reaction.price_war_likelihood), use_container_width=True)
            render_alert(run.competitive_reaction.expected_response, "info")
            st.markdown(f"**Mitigation:** {run.competitive_reaction.mitigation}")
            st.caption(f"Time horizon: {run.competitive_reaction.time_horizon}")

        with tabs[8]:
            ap = run.action_plan
            st.markdown(f'<div class="action-card"><strong>Primary Action:</strong> {ap.primary_action}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="action-card"><strong>Target Audience:</strong> {ap.target_audience}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="action-card"><strong>Pricing Tactic:</strong> {ap.pricing_tactic}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="action-card"><strong>First Test:</strong> {ap.first_test}</div>', unsafe_allow_html=True)
            if ap.platform_actions:
                st.markdown("**Platform-Specific Actions:**")
                for action in ap.platform_actions:
                    st.markdown(f"  - {action}")
            if ap.scale_projection:
                sp = ap.scale_projection
                st.markdown("---")
                st.markdown("### 📈 Scale This Business")
                sc1, sc2, sc3 = st.columns(3)
                with sc1: render_metric_card("Required Volume", f"{sp.required_volume} units/mo", sp.feasibility)
                with sc2: render_metric_card("Daily Ad Spend", format_currency(sp.required_daily_ad_spend), "To hit target")
                with sc3: render_metric_card("Monthly Marketing", format_currency(sp.total_monthly_marketing), f"Break-even: Month {sp.break_even_month or '?'}")
                for c in sp.constraints:
                    st.caption(c)

        with tabs[9]:
            for exp in rec.explanations:
                st.markdown(f"- {exp}")

        # Limitations
        render_limitations()

        # Export & Save
        st.markdown("---")
        ex1, ex2, ex3, ex4 = st.columns(4)
        with ex1:
            if st.button("💾 Save Analysis"):
                run_id = save_run(run)
                st.success(f"Saved! ID: {run_id}")
        with ex2:
            st.download_button("📄 Export JSON", export_json_bytes(run_data), file_name=f"{product_name}_analysis.json", mime="application/json")
        with ex3:
            st.download_button("📊 Export CSV", export_csv_bytes(run_data), file_name=f"{product_name}_simulation.csv", mime="text/csv")
        with ex4:
            st.download_button("📑 Export PDF", export_pdf_bytes(run_data, product_name), file_name=f"{product_name}_report.pdf", mime="application/pdf")


if __name__ == "__main__":
    main()
