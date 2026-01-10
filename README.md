# Industrial Telemetry Analytics Platform (ITAP)

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A production-oriented industrial analytics platform for **anomaly detection, explainability, aggregation, and operator-ready alerting** on time-series sensor data.

ITAP transforms raw telemetry into actionable intelligence by detecting anomalous behavior, explaining *why* anomalies occur, aggregating insights at device and fleet levels, and emitting high-quality alerts through declarative rules.

> **Design Philosophy:** Built to reflect real-world IoT/industrial analytics systems, not academic demos.

---

## 🎯 Project Overview

### What ITAP Does

Most anomaly detection systems stop at flagging outliers. ITAP goes further:

| Traditional Approach | ITAP Approach |
|---------------------|---------------|
| "Something is wrong" | **What** happened, **why** it happened, **how severe** it is |
| Per-event noise | Fleet-level patterns and device prioritization |
| Black-box scores | Feature attribution by sensor family |
| Alert fatigue | Rule-based, high-quality alerts with root cause |

### Key Features

- 🔍 **Anomaly Detection** - Unsupervised ML (Isolation Forest) trained on normal operation
- 🧠 **Explainability** - Per-event feature attribution with sensor family grouping
- 📊 **Aggregation** - Device and fleet-level health summaries
- 🚨 **Smart Alerting** - YAML-driven rules to reduce noise and increase operator trust
- 🔧 **Production-Ready** - Idempotent pipelines, reproducible artifacts, comprehensive logging

---

## 📋 Table of Contents

- [Key Capabilities](#-key-capabilities)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Usage Guide](#-usage-guide)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Outputs & Artifacts](#-outputs--artifacts)
- [Design Principles](#-design-principles)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## ⚡ Key Capabilities

### 1. Telemetry Simulation

Generate realistic multi-device industrial telemetry with controllable fault injection:

- **Configurable parameters**: Sampling rate, duration, device count
- **Operating states**: RUN, IDLE, MAINT
- **Fault types**: 
  - Bearing wear (gradual vibration increase)
  - Overheat drift (thermal runaway)
  - Power instability (voltage/current spikes)
  - Sensor dropout (missing data patterns)

### 2. Time-Series Feature Engineering

Extract meaningful features from raw sensor signals:

```python
# Features include:
- Rolling statistics (mean, std, min, max)
- Trend indicators (slope, drift)
- Deviation metrics (delta, z-score)
- Frequency-domain features (FFT energy, dominant frequency)
- Event counters (error streaks, state transitions)
```

**Signal Families**: RPM, Temperature, Voltage, Current, Vibration

All features are:
- ✅ Per-device isolated
- ✅ Time-aware (no leakage)
- ✅ Interpretable
- ✅ Deterministic

### 3. Anomaly Detection

Unsupervised learning pipeline optimized for industrial data:

- **Model**: StandardScaler + Isolation Forest
- **Training**: Normal operation data only
- **Output**: Continuous anomaly scores (higher = more anomalous)
- **Threshold Selection**: Automated recall/precision sweep
- **Serialization**: Fully reproducible via `joblib`

**Why Isolation Forest?**  
Robust to noise, fast training/inference, no labeled data required, works well with mixed-feature industrial data.

### 4. Explainability (Operator-Facing)

Every flagged anomaly includes human-readable explanations:

**Example Output:**
```
2026-01-01 05:31:10 | DEV-0006 | RUN | score=0.1852

Sensor Family Attribution:
  Voltage:      25.2%
  Temperature:  25.0%
  Current:      20.1%
  RPM:          16.2%
  Vibration:    10.3%

Top Contributing Features:
  voltage_v_trend:  6.0%
  voltage_v_mean:   6.0%
  voltage_v_min:    6.0%
  voltage_v_max:    5.5%
  temp_c_max:       5.3%
```

This answers: *"Why did the system flag this event?"*

### 5. Fleet & Device Aggregation

Move from individual events to strategic insights:

**Device-Level Summary:**
```
DEV-0006 | n=3 | avg_score=0.1765 | p95=0.1839
Dominant Families: Voltage=25.2%, Temperature=25.0%, Current=20.1%
```

**Enables:**
- 🏭 Fleet health dashboards
- 🔧 Maintenance prioritization
- 📈 Trend analysis
- 💰 Cost optimization

### 6. Intelligent Alerting

**Not all anomalies are alerts.** ITAP uses declarative rules to ensure high signal-to-noise ratio.

#### Alert Rule Types

**Burst Detection:**
```yaml
type: burst
device_window_minutes: 15
min_anomalies: 3
severity: critical
cause: "Repeated anomalies detected"
```

**Dominant Sensor Family:**
```yaml
type: dominant_family
family: Voltage
min_percent: 45
severity: critical
cause: "Power instability"
```

**Tagged Fault Routing:**
```yaml
type: tag_route
tag: bearing_wear
route: maintenance
severity: warning
cause: "Mechanical degradation"
```

**Alert Output:**
```
🔴 CRITICAL | 2026-01-01 05:31:10 | DEV-0006 | RUN
Score: 0.1852 | Confidence: 1.00
Root Cause: Power instability
Families: Voltage=24.7%, Temperature=24.6%, Current=20.2%
Rule: power_instability_voltage_current
```

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Telemetry Generator                       │
│              (Multi-device, fault injection)                 │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              Validation & Quality Checks                     │
│          (Schema, ranges, missing data analysis)             │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                 SQL Storage (SQLite)                         │
│              (Idempotent ingestion pipeline)                 │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│            Time-Series Feature Engineering                   │
│     (Rolling windows, FFT, trend, event counters)            │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│          Anomaly Scoring (Isolation Forest)                  │
│              (Trained on normal data only)                   │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│             Threshold Selection & Evaluation                 │
│          (Precision/Recall sweep, ROC-AUC)                   │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│         Explainability (Feature Attribution)                 │
│       (|z|-score contributions, sensor families)             │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│        Aggregation (Device & Fleet Summaries)                │
│    (Count, avg score, p95, dominant families)                │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│          Alert Generation (YAML-Driven Rules)                │
│   (Burst detection, family dominance, tag routing)           │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              Operator-Ready Artifacts                        │
│    (JSON: metrics, explanations, summaries, alerts)          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Virtual environment tool (`venv`, `conda`, etc.)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/itap.git
cd itap

# Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Basic Workflow

```bash
# 1. Generate synthetic telemetry
python -m itap.telemetry.run_generate

# 2. Validate data quality
python -m itap.validation.report

# 3. Ingest into database
python -m itap.storage.ingest

# 4. Train anomaly detection model
python -m itap.ml.run_train

# 5. Score, explain, aggregate, and alert
python -m itap.ml.run_score
```

---

## 📖 Usage Guide

### 1. Generate Telemetry

```bash
python -m itap.telemetry.run_generate
```

**Output:** `data/raw/telemetry_sample.csv`

**Configuration:** Edit `configs/local.example.yaml` to adjust:
- Number of devices
- Sampling frequency
- Simulation duration
- Fault injection parameters

### 2. Validate Data

```bash
python -m itap.validation.report
```

**Outputs:**
- Console summary (missing rates, range violations)
- `docs/validation_report_sample.json`

**Purpose:** Catch data quality issues before modeling

### 3. Ingest to Database

```bash
python -m itap.storage.ingest
```

**Behavior:**
- First run: Inserts all rows
- Subsequent runs: Inserts 0 rows (idempotent)

**Database:** SQLite (`itap.db`) - PostgreSQL compatible schema

### 4. Train Model

```bash
python -m itap.ml.run_train
```

**Output:** `artifacts/isoforest.joblib`

**Training Data:** Only `RUN` and `IDLE` states with `anomaly_tag == null` (normal operation)

**Model:** StandardScaler + IsolationForest (100 estimators, contamination=0.02)

### 5. Score & Generate Alerts

```bash
python -m itap.ml.run_score
```

**Outputs:**
- `artifacts/metrics.json` - Model performance metrics
- `artifacts/explanations_top.json` - Per-event feature attributions
- `artifacts/aggregate_summaries.json` - Device/fleet summaries
- `artifacts/alerts.json` - Operator-ready alerts

**Console Output:**
- Threshold sweep results
- Per-tag recall breakdown
- Top anomalous events with explanations
- Device aggregation summaries
- Alert feed

### 6. Run Tests

```bash
pytest -v
```

All tests should pass. Coverage focuses on:
- Feature engineering correctness
- Pipeline determinism
- Alert rule logic

---

## 📁 Project Structure

```
itap/
├── ml/                          # Machine learning pipeline
│   ├── anomaly.py              # Model definition & serialization
│   ├── features.py             # Time-series feature engineering
│   ├── evaluate.py             # Threshold optimization & metrics
│   ├── explain.py              # Explainability logic
│   ├── aggregate.py            # Fleet/device aggregation
│   ├── alerts.py               # Alert rule engine
│   ├── run_train.py            # Training script
│   └── run_score.py            # End-to-end scoring pipeline
│
├── telemetry/                   # Telemetry generation
│   ├── generator.py
│   ├── faults.py
│   └── run_generate.py
│
├── validation/                  # Data quality
│   ├── schema.py
│   ├── diagnostics.py
│   └── report.py
│
├── storage/                     # Database layer
│   ├── database.py             # SQLAlchemy session
│   ├── models.py               # ORM models
│   ├── ingest.py               # CSV → DB pipeline
│   └── query.py
│
configs/
├── local.example.yaml          # Simulation config
└── alert_rules.yaml            # Alert rule definitions
│
artifacts/                       # Generated outputs (gitignored)
├── isoforest.joblib
├── metrics.json
├── explanations_top.json
├── aggregate_summaries.json
└── alerts.json
│
data/
└── raw/                        # Generated telemetry (gitignored)
│
docs/
└── validation_report_sample.json
│
tests/
├── test_features.py
├── test_validation.py
└── test_alerts.py
│
requirements.txt
pytest.ini
README.md
LICENSE
```

---

## ⚙️ Configuration

### Alert Rules (`configs/alert_rules.yaml`)

Define custom alert logic without code changes:

```yaml
rules:
  - name: critical_burst
    type: burst
    device_window_minutes: 15
    min_anomalies: 3
    severity: critical
    cause: "Multiple anomalies in short time window"
    
  - name: voltage_instability
    type: dominant_family
    family: Voltage
    min_percent: 40
    severity: warning
    cause: "Power supply issues detected"
    
  - name: bearing_maintenance
    type: tag_route
    tag: bearing_wear
    route: maintenance
    severity: warning
    cause: "Mechanical degradation - schedule inspection"
```

### Simulation Config (`configs/local.example.yaml`)

```yaml
telemetry:
  devices: 10
  duration_hours: 48
  sample_rate_seconds: 60
  
faults:
  injection_rate: 0.05
  types:
    - bearing_wear
    - overheat
    - power_spike
```

---

## 📦 Outputs & Artifacts

All artifacts are JSON for easy integration with dashboards, APIs, and monitoring tools.

### `artifacts/metrics.json`
```json
{
  "threshold": 0.1234,
  "precision": 0.82,
  "recall": 0.91,
  "f1": 0.86,
  "roc_auc": 0.94
}
```

### `artifacts/alerts.json`
```json
[
  {
    "timestamp": "2026-01-01 05:31:10",
    "device_id": "DEV-0006",
    "severity": "CRITICAL",
    "root_cause": "Power instability",
    "score": 0.1852,
    "confidence": 1.00,
    "families": [["Voltage", 24.7], ["Temperature", 24.6]],
    "rule_name": "power_instability_voltage_current"
  }
]
```

### `artifacts/aggregate_summaries.json`
```json
[
  {
    "group_key": "DEV-0006",
    "n_flagged": 3,
    "avg_score": 0.1765,
    "p95_score": 0.1839,
    "top_families": [["Voltage", 25.2], ["Temperature", 25.0]]
  }
]
```

---

## 💡 Design Principles

1. **Explainability Over Black-Box Accuracy**  
   Operators need to understand *why*, not just *what*

2. **Alert Quality Over Quantity**  
   High-confidence, actionable alerts reduce fatigue

3. **Operator Trust Through Transparency**  
   Feature attribution and rule visibility build confidence

4. **Data-Driven Configuration**  
   YAML rules enable non-engineers to tune alerting

5. **Production Realism**  
   Idempotent pipelines, error handling, comprehensive logging

6. **Separation of Concerns**  
   ML scoring ≠ alerting logic. Each layer has clear responsibility.

---

## 🗺 Roadmap

### Near-Term Enhancements
- [ ] Streamlit dashboard for fleet visualization
- [ ] Alert delivery integrations (Slack, email, PagerDuty)
- [ ] PostgreSQL backend support
- [ ] Docker containerization
- [ ] CI/CD pipeline (GitHub Actions)

### Advanced Features
- [ ] Streaming inference (Kafka/MQTT)
- [ ] Seasonal decomposition (STL)
- [ ] Multi-model ensemble (Autoencoder, LSTM-VAE)
- [ ] Concept drift detection
- [ ] Forecasting (temperature, vibration trends)
- [ ] Auto-remediation hooks

---

## 🤝 Contributing

Contributions are welcome! This project is designed as a portfolio piece but also serves as a learning resource for industrial ML systems.

**Areas for contribution:**
- Additional fault injection patterns
- New alert rule types
- Dashboard improvements
- Documentation
- Test coverage

Please open an issue first to discuss proposed changes.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Jose Santana**  
Entry-Level Software / Systems Engineer

**Focus Areas:**
- Industrial Analytics & IoT
- Data Engineering
- ML Systems Design
- Explainable AI

**Contact:** [Your LinkedIn/Email]

---

## 🙏 Acknowledgments

- Scikit-learn for robust ML primitives
- SQLAlchemy for elegant ORM design
- Industrial IoT community for domain insights

---

**Built with care to demonstrate production-ready industrial ML systems.** ⚙️
