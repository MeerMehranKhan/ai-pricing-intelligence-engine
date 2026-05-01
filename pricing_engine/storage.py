"""
SQLite Storage Module with Multi-Run Comparison.

Handles persistence of analysis runs, version history, run comparison,
delta analysis, and trend detection.
"""

from __future__ import annotations
import json
import sqlite3
import uuid
from datetime import datetime
from typing import Optional
from pricing_engine.models import AnalysisRun, RunComparison
from pricing_engine.utils import model_to_dict

DB_PATH = "pricing_engine.db"


def _get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    _init_tables(conn)
    return conn


def _init_tables(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analysis_runs (
            id TEXT PRIMARY KEY,
            product_name TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            version INTEGER DEFAULT 1,
            input_json TEXT NOT NULL,
            results_json TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS export_log (
            id TEXT PRIMARY KEY,
            run_id TEXT,
            format TEXT,
            filepath TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()


def save_run(run: AnalysisRun, db_path: str = DB_PATH) -> str:
    """Save an analysis run. Returns the run ID."""
    conn = _get_connection(db_path)
    run_id = run.id or str(uuid.uuid4())[:12]
    # Determine version
    cursor = conn.execute(
        "SELECT MAX(version) FROM analysis_runs WHERE product_name = ?",
        (run.product_input.name,)
    )
    row = cursor.fetchone()
    version = (row[0] or 0) + 1

    run_data = model_to_dict(run)
    input_data = model_to_dict(run.product_input)

    conn.execute(
        "INSERT INTO analysis_runs (id, product_name, timestamp, version, input_json, results_json) VALUES (?, ?, ?, ?, ?, ?)",
        (run_id, run.product_input.name, run.timestamp.isoformat(), version, json.dumps(input_data), json.dumps(run_data)),
    )
    conn.commit()
    conn.close()
    return run_id


def load_run(run_id: str, db_path: str = DB_PATH) -> Optional[dict]:
    """Load a saved analysis run by ID."""
    conn = _get_connection(db_path)
    cursor = conn.execute("SELECT * FROM analysis_runs WHERE id = ?", (run_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "id": row["id"], "product_name": row["product_name"],
            "timestamp": row["timestamp"], "version": row["version"],
            "input": json.loads(row["input_json"]),
            "results": json.loads(row["results_json"]),
        }
    return None


def list_runs(db_path: str = DB_PATH) -> list[dict]:
    """List all saved runs ordered by timestamp descending."""
    conn = _get_connection(db_path)
    cursor = conn.execute("SELECT id, product_name, timestamp, version FROM analysis_runs ORDER BY timestamp DESC")
    runs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return runs


def delete_run(run_id: str, db_path: str = DB_PATH) -> bool:
    """Delete a saved run by ID."""
    conn = _get_connection(db_path)
    conn.execute("DELETE FROM analysis_runs WHERE id = ?", (run_id,))
    conn.commit()
    affected = conn.total_changes
    conn.close()
    return affected > 0


def compare_runs(run_a_id: str, run_b_id: str, db_path: str = DB_PATH) -> Optional[RunComparison]:
    """Compare two analysis runs and explain differences."""
    a = load_run(run_a_id, db_path)
    b = load_run(run_b_id, db_path)
    if not a or not b:
        return None

    a_res = a["results"]
    b_res = b["results"]
    a_rec = a_res.get("recommendation", {})
    b_rec = b_res.get("recommendation", {})

    price_a = a_rec.get("recommended_price", 0)
    price_b = b_rec.get("recommended_price", 0)
    margin_a = a_rec.get("contribution_margin_pct", 0)
    margin_b = b_rec.get("contribution_margin_pct", 0)
    profit_a = a_rec.get("profit_estimate", 0)
    profit_b = b_rec.get("profit_estimate", 0)
    risk_a = a_rec.get("risk", {}).get("score", 0)
    risk_b = b_rec.get("risk", {}).get("score", 0)

    # Detect input changes
    input_changes = []
    a_in = a["input"]
    b_in = b["input"]
    for key in ["cost", "platform", "category", "positioning"]:
        if a_in.get(key) != b_in.get(key):
            input_changes.append(f"{key}: {a_in.get(key)} -> {b_in.get(key)}")

    # Impact summary
    profit_delta = profit_b - profit_a
    if abs(profit_delta) > 0.01:
        direction = "increased" if profit_delta > 0 else "decreased"
        impact = f"Profit {direction} by ${abs(profit_delta):.2f}."
        if input_changes:
            impact += f" Changes: {', '.join(input_changes)}."
    else:
        impact = "No significant profit change between runs."

    better = run_b_id if profit_b > profit_a else run_a_id

    return RunComparison(
        run_a_id=run_a_id, run_b_id=run_b_id,
        price_delta=round(price_b - price_a, 2),
        margin_delta=round(margin_b - margin_a, 4),
        profit_delta=round(profit_delta, 2),
        risk_delta=round(risk_b - risk_a, 1),
        input_changes=input_changes,
        impact_summary=impact, better_run=better,
    )


def log_export(run_id: str, fmt: str, filepath: str, db_path: str = DB_PATH):
    """Log an export event."""
    conn = _get_connection(db_path)
    conn.execute(
        "INSERT INTO export_log (id, run_id, format, filepath, timestamp) VALUES (?, ?, ?, ?, ?)",
        (str(uuid.uuid4())[:12], run_id, fmt, filepath, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
