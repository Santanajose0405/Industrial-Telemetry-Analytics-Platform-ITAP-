# Industrial Telemetry Analytics Platform (ITAP)

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-70%2B-brightgreen.svg)](tests/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Operator-ready anomaly detection, explainability, and alerting for industrial telemetry.**

Transform raw sensor data into high-quality, explainable alerts that operators trust.

---

## 🎯 Overview

ITAP is an end-to-end analytics platform that converts raw industrial telemetry into **high-quality, explainable alerts** suitable for real operational environments.

Unlike raw anomaly detection systems that simply flag outliers, ITAP emphasizes:

- ✅ **Alert quality over volume** – fewer, more actionable alerts  
- ✅ **Explainability over black-box scores** – every alert includes root cause analysis  
- ✅ **Operational ownership** – automatic routing to responsible teams  
- ✅ **Test-driven reliability** – 70+ unit tests ensure correctness  

At a high level:

```text
Raw Telemetry → Smart Detection → Root Cause Analysis → Team Routing → Actionable Alerts
Result: Operators receive fewer alerts, understand each one, and know exactly who should respond.

🚀 Key Capabilities
1. Intelligent Alerting
Three alert types, all configurable via YAML:

Burst Detection – triggers when N anomalies occur within M minutes for a device

Example: 3 events within 15 minutes → Critical burst alert

Prevents single-event noise

Per-device tracking

Dominant Sensor Family – triggers when specific sensor contributions exceed thresholds

Example: Voltage > 45% → Power instability alert

Weighted confidence scoring

Multi-family rules (e.g., Voltage + Current)

Tagged Fault Routing – routes known fault types to appropriate teams

bearing_wear → Maintenance team

overheat_drift → Thermal team

power_spike → Electrical team

All rules are:

✅ YAML-configured (no code changes required)

✅ Validated at startup (fail-fast)

✅ Confidence-scored to reduce false positives

2. Explainability
Every alert includes rich attribution:

text
Copy code
Alert: Power instability detected
Device: DEV-0006
Score: 0.1852
Confidence: 1.00

Root Cause Attribution:
  Voltage:      24.7%  ← Dominant contributor
  Temperature:  24.6%
  Current:      20.2%

Top Contributing Features:
  voltage_v_trend:  5.9%
  voltage_v_mean:   5.9%
  voltage_v_min:    5.9%
  temp_c_max:       5.3%
Benefits:

Operators understand why the system flagged an event

Feature attribution guides troubleshooting

Sensor family grouping provides domain context

All explanations are persisted for audit trails

3. Fleet & Device Aggregation
Move from individual events to strategic insights.

Device-level summaries:

DEV-0006 | n=3 events | avg_score=0.1765 | p95=0.1839
Dominant Patterns: Voltage=25.2%, Temperature=25.0%, Current=20.1%
Fleet-level insights:

Health rankings across devices

Failure mode patterns

Maintenance prioritization

Trend analysis

Use cases:

🏭 Fleet health dashboards

🔧 Predictive maintenance planning

📈 Reliability engineering

💰 Cost optimization

4. Operator-Ready API & Web Dashboard
FastAPI Backend
The backend exposes read-only endpoints powered by JSON artifacts in artifacts/:

GET /api/health       # Health + artifact presence & freshness
GET /api/overview     # High-level fleet KPIs (derived from artifacts)
GET /api/alerts       # Alerts view (backed by alerts.json)
GET /api/aggregates   # Fleet & device aggregates (aggregate_summaries.json)
GET /api/metrics      # Model performance metrics (metrics.json)
Features:

Typed responses via Pydantic models

CORS-enabled for frontend use

Artifact-backed (no database required)

Easy to swap artifacts for a real DB later

React Operator Dashboard (Vite + TypeScript)
The itap-dashboard/ app is a modern single-page UI for operators:

Health page

Calls /api/health

Shows overall status, artifacts present/missing, per-artifact freshness

Highlights stale/missing artifacts based on per-file SLAs

One-click “Copy diagnostics JSON” button for tickets

Overview page

Summarized KPIs from /api/overview

High-level status of the anomaly pipeline

Uses the same health diagnostics, but distilled into operator-friendly cards

Alerts page

Table view for recent alerts (wired to /api/alerts)

Severity, device, route, message columns

Currently seeded with mock data but layout matches the API

Aggregates page

Fleet/device aggregates from /api/aggregates

Bucketed summaries (e.g., last 1h / 24h) to support reliability/maintenance views

Metrics page

Time-series and KPI visualizations from /api/metrics

Uses Recharts to display anomaly rate and related metrics

Tech stack:

Vite + React + TypeScript

@tanstack/react-query for data fetching & caching

Tailwind CSS for styling

Recharts for charts

🏗 Architecture

┌─────────────────────────────────────────────────────────────┐
│                    Telemetry Data                          │
│              (CSV, SQL, or streaming)                      │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                  Model Scoring                             │
│         (Isolation Forest, artifact-based)                 │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              Explainability Engine                         │
│     (Feature attribution, sensor family grouping)          │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                 Alert Rules (YAML)                         │
│    (Burst, dominant family, routing evaluation)            │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                   Aggregation                              │
│          (Fleet and device-level summaries)                │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              API & Web Dashboard                           │
│     (FastAPI backend + React operator dashboard)           │
└─────────────────────────────────────────────────────────────┘
Technology stack:

Model: Scikit-learn Isolation Forest

Rules: YAML-configured, Python dataclasses

API: FastAPI + Pydantic

Dashboard: React (Vite, TS, Tailwind, Recharts)

Tests: Pytest with 70+ unit tests

Storage: Artifact-based JSON, DB-ready schema

📁 Project Structure

itap/
├── api/                        # FastAPI service
│   └── main.py                 # REST endpoints (/api/*)
│
├── dashboard/                  # (Optional) Streamlit UI prototype
│   ├── app.py
│   └── views/
│
├── ml/                         # Core ML pipeline
│   ├── anomaly.py
│   ├── features.py
│   ├── explain.py
│   ├── aggregate.py
│   ├── alerts.py
│   ├── evaluate.py
│   ├── run_train.py
│   └── run_score.py
│
├── storage/                    # Data layer (DB-ready)
│   ├── database.py
│   ├── models.py
│   └── ingest.py
│
├── telemetry/                  # Data generation
│   ├── generator.py
│   └── faults.py
│
configs/
├── alert_rules.yaml            # Declarative alert configuration
└── local.example.yaml          # Simulation parameters
│
tests/                          # Comprehensive test suite
├── conftest.py
├── test_alert_rules_config.py
├── test_alert_rules_burst.py
├── test_alert_rules_dominant_family.py
├── test_alert_rules_routing.py
└── README.md
│
artifacts/                      # Generated outputs (gitignored)
├── isoforest.joblib            # Trained model
├── metrics.json                # Performance metrics
├── explanations_top.json       # Top event explanations
├── aggregate_summaries.json    # Device/fleet summaries
└── alerts.json                 # Operator-ready alerts
│
itap-dashboard/                 # React operator dashboard (Vite + TS)
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig*.json
├── public/
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── api/
    │   └── client.ts           # fetchJson + API helpers
    ├── lib/
    │   └── schemas/            # zod schemas for /api/* responses
    ├── components/             # Layout, nav, stat cards, loading/error states
    └── pages/                  # Overview, Alerts, Aggregates, Metrics, Health
│
README.md                       # This file
requirements.txt                # Python dependencies
pytest.ini                      # Test configuration

🏃 Running the Platform

0. Prerequisites
Python side:

python --version  # 3.9+
python -m venv .venv
.venv\Scripts\activate      # Windows
# or: source .venv/bin/activate
pip install -r requirements.txt
Node/JS side (for the React dashboard):

Node.js 18+ recommended (Node 20/22 also fine)

npm 9+ (comes with Node)

Inside itap-dashboard/ you’ll run npm install once.

1. Generate Telemetry (optional)
python -m itap.telemetry.run_generate
Output: data/raw/telemetry_sample.csv

2. Train the Model
python -m itap.ml.run_train
Output: artifacts/isoforest.joblib

3. Score & Generate Artifacts
python -m itap.ml.run_score
Outputs (all in artifacts/):

metrics.json – model performance

explanations_top.json – event explainability

aggregate_summaries.json – fleet summaries

alerts.json – operator alerts

4. Start the API
From the repo root:

uvicorn itap.api.main:app --reload
Access:

API root: http://localhost:8000

OpenAPI docs: http://localhost:8000/docs

5. Start the React Operator Dashboard
From the repo root:

cd itap-dashboard
npm install          # first time only
npm run dev
Access: http://localhost:5173

Pages:

/ or /overview – KPIs & high-level pipeline status

/health – artifact presence, freshness SLAs, and diagnostics copy button

/alerts – alerts table (ready for /api/alerts)

/aggregates – fleet aggregates (ready for /api/aggregates)

/metrics – model metrics and trend chart (ready for /api/metrics)

6. (Optional) Legacy Streamlit Dashboard
If you want to run the original Streamlit prototype:

streamlit run itap/dashboard/app.py
Access: http://localhost:8501

🧪 Testing

pytest -v
# or with coverage:
pytest --cov=itap.ml.alerts --cov-report=html
What’s covered:

Alert rule validation

Burst detection (time windows, per-device isolation, edge cases)

Dominant family logic & confidence scoring

Tag routing and severity assignment

70+ tests lock in both the business rules and edge-case behaviours.

💡 Design Philosophy
1. Alerts Should Be Actionable
Bad alert:

Anomaly detected on DEV-0006
Score: 0.1852
ITAP alert:

CRITICAL: Power instability on DEV-0006
Root Cause: Voltage=24.7%, Current=20.2%
Assigned to: Electrical Team
Confidence: 1.00
Action: Inspect power supply connections
2. Operators Should Understand Why
Every alert includes root-cause attribution, feature contributions, and historical context.
If an engineer can’t explain an alert in plain language, the system hasn’t done its job.

3. Systems Should Fail Loudly, Not Silently
Invalid YAML config? You get a clear error on startup, not a mysterious lack of alerts.

4. Rules Should Be Data, Not Code
Operators can tune configs/alert_rules.yaml without touching Python.
Changes are auditable and deployable like any other config.

5. Tests Define Correctness
Tests are written as executable documentation for business rules.
If a behaviour is important, it gets a test.

📊 Performance Metrics (Example)
Precision: 82%

Recall: 91%

F1 Score: 86%

ROC-AUC: 94%

Alert quality:

~70% reduction in alert volume vs threshold-based rules

100% of alerts include root cause

Avg confidence: 0.87

🤝 Contributing
Contributions welcome! Interesting areas:

New fault injection patterns

Additional alert rule types (e.g., rate-of-change)

Dashboard enhancements (filters, search, auth)

Integration tests, CI/CD, Docker

Please open an issue first to discuss substantial changes.

📄 License
MIT License – see LICENSE for details.

👤 Author
Jose Santana
Entry-Level Software / Systems Engineer

Focus areas:

Industrial Analytics & IoT

ML Systems Design

Data Engineering

Explainable AI

Contact: LinkedIn

Built to demonstrate production-ready ML systems engineering—from raw telemetry to an operator’s dashboard.

“Good alerts are invisible when things work, and invaluable when they don't.”