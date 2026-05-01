"""
Reporting Module — PDF, CSV, JSON Export.

Generates formatted export files from analysis results.
PDF uses fpdf2 with graceful fallback to HTML.
"""

from __future__ import annotations
import csv
import io
import json
import os
from datetime import datetime
from typing import Any
from pricing_engine.utils import model_to_dict, format_currency, format_percentage

EXPORT_DIR = "exports"


def ensure_export_dir():
    os.makedirs(EXPORT_DIR, exist_ok=True)


def export_json(run_data: dict, filename: str = None) -> str:
    """Export full analysis as JSON."""
    ensure_export_dir()
    if not filename:
        filename = f"analysis_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(EXPORT_DIR, filename)
    with open(filepath, "w") as f:
        json.dump(run_data, f, indent=2, default=str)
    return filepath


def export_json_bytes(run_data: dict) -> bytes:
    """Export full analysis as JSON bytes for download."""
    return json.dumps(run_data, indent=2, default=str).encode("utf-8")


def export_csv_bytes(run_data: dict) -> bytes:
    """Export simulation data as CSV bytes for download."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Simulation data
    sim = run_data.get("simulation", {})
    if sim:
        writer.writerow(["Price", "Demand", "Revenue", "Total Cost", "Profit"])
        prices = sim.get("price_points", [])
        demands = sim.get("demand", [])
        revenues = sim.get("revenue", [])
        costs = sim.get("total_cost", [])
        profits = sim.get("profit", [])
        for i in range(len(prices)):
            writer.writerow([
                prices[i] if i < len(prices) else "",
                demands[i] if i < len(demands) else "",
                revenues[i] if i < len(revenues) else "",
                costs[i] if i < len(costs) else "",
                profits[i] if i < len(profits) else "",
            ])

    writer.writerow([])
    writer.writerow(["--- Recommendation Summary ---"])
    rec = run_data.get("recommendation", {})
    if rec:
        writer.writerow(["Recommended Price", rec.get("recommended_price", "")])
        writer.writerow(["Min Safe Price", rec.get("min_safe_price", "")])
        writer.writerow(["Max Safe Price", rec.get("max_safe_price", "")])
        writer.writerow(["Contribution Margin %", rec.get("contribution_margin_pct", "")])
        writer.writerow(["Confidence Score", rec.get("confidence_score", "")])

    return output.getvalue().encode("utf-8")


def export_pdf_bytes(run_data: dict, product_name: str = "Product") -> bytes:
    """Export formatted PDF report. Falls back to text if fpdf2 fails."""
    try:
        from fpdf import FPDF

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Title
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 12, "AI Pricing Intelligence Report", ln=True, align="C")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 8, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", ln=True, align="C")
        pdf.cell(0, 8, f"Product: {product_name}", ln=True, align="C")
        pdf.ln(10)

        # Recommendation
        rec = run_data.get("recommendation", {})
        if rec:
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 10, "Pricing Recommendation", ln=True)
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 7, f"Recommended Price: {format_currency(rec.get('recommended_price', 0))}", ln=True)
            pdf.cell(0, 7, f"Safe Range: {format_currency(rec.get('min_safe_price', 0))} - {format_currency(rec.get('max_safe_price', 0))}", ln=True)
            pdf.cell(0, 7, f"Contribution Margin: {format_percentage(rec.get('contribution_margin_pct', 0))}", ln=True)
            pdf.cell(0, 7, f"Confidence: {rec.get('confidence_score', 0):.0f}/100", ln=True)
            risk = rec.get("risk", {})
            pdf.cell(0, 7, f"Risk Level: {risk.get('level', 'Medium')}", ln=True)
            pdf.ln(5)

        # Strategy
        strategy = run_data.get("strategy", {})
        if strategy:
            selected = strategy.get("selected", {})
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 10, "Strategy Recommendation", ln=True)
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 7, f"Strategy: {selected.get('name', 'N/A')}", ln=True)
            pdf.multi_cell(0, 7, f"Rationale: {selected.get('rationale', '')}")
            pdf.ln(5)

        # Explanations
        explanations = run_data.get("recommendation", {}).get("explanations", [])
        if explanations:
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 10, "Detailed Analysis", ln=True)
            pdf.set_font("Helvetica", "", 10)
            for exp in explanations:
                pdf.multi_cell(0, 6, f"  {exp}")
                pdf.ln(2)

        # Disclaimer
        pdf.ln(10)
        pdf.set_font("Helvetica", "I", 9)
        pdf.multi_cell(0, 5,
            "Disclaimer: This analysis uses heuristic models, not real-time market data. "
            "Demand estimates are directional approximations. Results should be validated "
            "with real-world pricing tests."
        )

        return bytes(pdf.output())

    except Exception:
        # Fallback to plain text
        lines = [
            "AI Pricing Intelligence Report",
            f"Product: {product_name}",
            f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            "",
        ]
        rec = run_data.get("recommendation", {})
        if rec:
            lines.append(f"Recommended Price: {format_currency(rec.get('recommended_price', 0))}")
            lines.append(f"Confidence: {rec.get('confidence_score', 0):.0f}/100")
        return "\n".join(lines).encode("utf-8")
