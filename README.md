# AI Pricing Intelligence Engine

A **decision-grade pricing intelligence system** for e-commerce products. Not a generic pricing calculator -- this is a tool that analyzes market conditions, computes real unit economics, tests business fragility, and delivers actionable go/no-go pricing decisions.

Built for e-commerce sellers, dropshippers, startup founders, and product managers who need to make high-impact pricing decisions with confidence.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red?logo=streamlit)
![Tests](https://img.shields.io/badge/Tests-55+-green?logo=pytest)
![License](https://img.shields.io/badge/License-MIT-yellow)

## What This Does

- Analyzes competitor pricing with clustering, gap detection, and density scoring
- Computes full unit economics (COGS + shipping + packaging + platform fees + processing + returns + CAC)
- Estimates price elasticity with demand curves and uncertainty bands
- Calibrates outputs against real-world industry benchmarks
- Selects and validates pricing strategies with positioning alignment
- Runs profit simulations across 50 price points
- Tests business fragility with sensitivity analysis (tornado charts)
- Models competitive reactions and price war likelihood
- Projects 90-day revenue timeline with launch/growth/stable phases
- Generates three scenario plans (Conservative / Balanced / Aggressive)
- Enforces a hard-stop viability gate (Go / Caution / No-Go)
- Provides a scale projector ("What does $10k/month look like?")
- Exports to PDF, CSV, and JSON

## What This Is NOT

- Not a real-time scraper or live market data feed
- Not a guaranteed-profit tool or financial advisor
- Not a replacement for real-world A/B testing
- Not product-specific -- uses category-level heuristics, not measured data

## Quick Start

```bash
# Clone the repository
git clone https://github.com/MeerMehranKhan/ai-pricing-intelligence-engine.git
cd ai-pricing-intelligence-engine

# Create and activate a virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

No API keys required. The engine works fully out of the box using deterministic heuristics.

## Optional: LLM-Enhanced Explanations

For richer narrative explanations, copy `.env.example` to `.env` and add your API keys:

```bash
cp .env.example .env
# Edit .env with your keys
```

Supports OpenAI and Anthropic. The app falls back gracefully to local mode if keys are missing.

## Architecture

```text
ai-pricing-intelligence-engine/
|-- app.py                          # Streamlit entry point
|-- pricing_engine/
|   |-- config.py                   # Constants, fees, benchmarks
|   |-- models.py                   # Pydantic data models (30+ types)
|   |-- utils.py                    # Shared utilities
|   |-- ingestion.py                # Input validation + CSV import
|   |-- cleaning.py                 # Data cleaning + outlier removal
|   |-- unit_economics.py           # Full cost structure engine
|   |-- market_analysis.py          # Competitor clustering + gaps
|   |-- positioning.py              # Budget/Mid/Premium positioning
|   |-- elasticity.py               # Demand curves + constraints
|   |-- calibration.py              # Industry benchmark validation
|   |-- pricing_strategy.py         # Strategy scoring + validation
|   |-- simulations.py              # Profit sims + scenarios + timeline
|   |-- sensitivity_analysis.py     # Fragility testing + tornado data
|   |-- competitive_reaction.py     # Competitor response modeling
|   |-- data_quality.py             # Input quality scoring
|   |-- recommendations.py          # Final recommendation + viability gate
|   |-- actions.py                  # Action plan + scale projector
|   |-- explanations.py             # Explainability + consistency check
|   |-- storage.py                  # SQLite persistence + comparison
|   |-- reporting.py                # PDF/CSV/JSON export
|   |-- charts.py                   # Plotly chart builders (8 types)
|   |-- ui_helpers.py               # Streamlit styled components
|-- tests/                          # pytest test suite (10 files, 55+ tests)
|-- data/
|   |-- sample_products.json        # 5 demo products with realistic data
```

## Key Features

### Unit Economics (Not Just Revenue Minus COGS)

Every calculation uses fully-loaded costs:

- COGS + Shipping + Packaging + Platform Fees + Payment Processing + Returns Buffer + CAC
- Contribution margin, break-even CAC, and profit-after-marketing at every price point

### Business Viability Gate

Hard-stop logic prevents recommending unprofitable products:

- Profit < 0? Force **No-Go**
- Margin < 15%? **High Risk Warning**
- Break-even CAC < $2? **Scalability Warning**
- Worst-case profit < 0? **Fragility Warning**

### Data Transparency

Every output is tagged with its reliability source:

- **Deterministic**: Computed from user-provided data
- **Estimated**: Derived from category heuristics
- **AI-Generated**: LLM-produced text (never math)

### When NOT to Trust This Model

- You have zero competitor data and are in a novel category
- Your product has no close substitutes (monopoly pricing is different)
- You are entering regulated markets with price controls
- You need real-time market pricing (this uses static inputs)

## Running Tests

```bash
pytest tests/ -v --tb=short
```

## Example Use Cases

- E-commerce seller evaluating a new Amazon private-label product
- Shopify brand testing price points for a new SKU launch
- Dropshipper deciding whether a product is worth sourcing
- Product manager building a pricing strategy for a SaaS add-on

## Tech Stack

| Component | Technology |
| --------- | ---------- |
| Language | Python 3.11+ |
| UI Framework | Streamlit |
| Data Models | Pydantic v2 |
| Visualizations | Plotly |
| ML (clustering) | scikit-learn |
| Storage | SQLite |
| PDF Export | fpdf2 |
| Testing | pytest |

## License

MIT License. See LICENSE for details.
