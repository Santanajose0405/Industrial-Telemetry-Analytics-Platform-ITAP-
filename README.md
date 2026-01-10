# Industrial Telemetry Analytics Platform (ITAP)

A production-oriented industrial analytics system that **detects, explains, aggregates, and alerts on anomalous behavior** in time-series telemetry data.

ITAP combines unsupervised machine learning with operator-friendly diagnostics to move beyond simple anomaly flags into **actionable intelligence**.

---

## Why ITAP?

Most anomaly detection systems stop at:
> "Something looks weird."

**ITAP answers:**
- **What happened?** (Per-event explainability)
- **Why did it happen?** (Feature attribution by sensor family)
- **How severe is it?** (Rule-based severity levels)
- **Is it systemic or isolated?** (Fleet-level aggregation)
- **What should an operator do next?** (Root cause identification)

This platform is designed to feel **operator-ready**, not experimental.

---

## Core Capabilities

### 1. Telemetry Simulation & Ingestion
- Multi-device time-series generation with controllable fault injection
- Realistic operating states (RUN, IDLE, MAINT)
- Fault types: overheat drift, bearing wear, power spikes, sensor dropouts
- Schema validation before storage
- Idempotent SQL ingestion pipeline

### 2. Time-Series Feature Engineering
- Rolling-window statistical features (mean, std, min, max)
- Trend and seasonality decomposition
- Delta and z-score deviation indicators
- Frequency-domain features (FFT energy, dominant frequency bins)
- Event-based counters (error streaks, state transitions, time-since-event)
- All features are per-device, time-aligned, and leakage-safe

### 3. Unsupervised Anomaly Detection
- Isolation Forest–based scoring pipeline
- Trained only on normal operating data
- Produces continuous anomaly scores (higher = more anomalous)
- Model-agnostic design (StandardScaler + IsolationForest)
- Scales across devices and operating states

### 4. Threshold Optimization
- Automated threshold sweep across score percentiles
- Precision, recall, F1, ROC-AUC metrics
- Operator-friendly selection (prioritizes recall, then precision)
- Per-fault-type recall diagnostics
- Best threshold persisted for production use

### 5. Explainability (Operator-Facing)
For each anomalous event, ITAP provides:
- **Top contributing features** with normalized % attribution
- **Sensor family grouping** (Voltage, Temperature, Current, RPM, Vibration)
- **Human-readable explanations** instead of raw model internals

**Example output:**
```
- 2026-01-01 05:31:10 | DEV-0006 | RUN | tag=power_spike | score=0.185200 | pred=1
    Families: Voltage=24.7%, Temperature=24.6%, Current=20.2%
    voltage_v_trend: 5.9%
    voltage_v_mean: 5.9%
    voltage_v_min: 5.9%
    voltage_v_max: 5.4%
    temp_c_max: 5.2%
```

### 6. Aggregation (Fleet & Device Level)
Anomalies are aggregated to surface **patterns**, not just individual spikes.

Per-device summaries include:
- Number of flagged events
- Average and 95th-percentile anomaly scores
- Dominant sensor families (normalized across all events)

**Example output:**
```
Fleet/Device Aggregations
- DEV-0006 | n=3 | avg_score=0.1765 | p95=0.1839 | Voltage=25.2%, Temperature=25.0%, Current=20.1%
- DEV-0003 | n=2 | avg_score=0.1623 | p95=0.1712 | Vibration=28.4%, RPM=22.1%, Temperature=19.3%
```

This enables:
- Device-level health triage
- Fleet-wide reliability assessment
- Predictive maintenance prioritization

### 7. Alerting (Rule-Based + ML Hybrid)
Alerts combine anomaly scores with deterministic rule logic based on sensor family dominance.

**Alert rules include:**
- Power instability (Voltage + Current dominance)
- Thermal overload (Temperature dominance)
- Mechanical wear (Vibration + RPM dominance)
- Electrical noise (Voltage dominance)
- Fallback rule for uncategorized anomalies

**Example alert:**
```
CRITICAL | 2026-01-01 05:31:10 | DEV-0006 | RUN | score=0.1852
cause=Power instability | conf=1.00 | Voltage=24.7%, Temperature=24.6%, Current=20.2%
    voltage_v_trend: 5.9%
    voltage_v_mean: 5.9%
    tag=power_spike
    rule=power_instability_voltage_current
```

Each alert provides:
- **Severity** (INFO / WARNING / CRITICAL)
- **Root cause** identification
- **Confidence score** (rule match strength)
- **Timestamp and device context**
- **Top contributing features**

---

## System Architecture

```
Telemetry Generator
    ↓
Validation & Diagnostics
    ↓
CSV Ingestion Pipeline (Idempotent)
    ↓
SQL Storage (SQLite / PostgreSQL-ready)
    ↓
Rolling-Window Feature Engineering
    ↓
Anomaly Scoring (Isolation Forest)
    ↓
Threshold Selection & Evaluation
    ↓
Per-Event Explainability
    ↓
Fleet/Device Aggregation
    ↓
Alert Generation & Severity Classification
    ↓
JSON Artifacts & Operator Output
```

---

## Repository Structure

```
itap/
├── telemetry/              # Telemetry simulation & fault injection
│   ├── generator.py
│   ├── faults.py
│   └── run_generate.py
│
├── validation/             # Schema, missing data, and range validation
│   ├── schema.py
│   ├── diagnostics.py
│   └── report.py
│
├── storage/                # SQL models, database config, ingestion
│   ├── database.py
│   ├── models.py
│   ├── ingest.py
│   └── query.py
│
├── ml/                     # Feature engineering, training, scoring, evaluation
│   ├── features.py         # Time-series feature extraction
│   ├── anomaly.py          # Isolation Forest pipeline
│   ├── evaluate.py         # Threshold sweep & metrics
│   ├── explain.py          # Per-event explainability
│   ├── aggregate.py        # Fleet/device aggregation
│   ├── alerts.py           # Alert rules & severity classification
│   ├── run_train.py        # Model training script
│   └── run_score.py        # Scoring & diagnostics script
│
├── configs/
│   └── local.example.yaml
│
├── data/
│   └── raw/                # Generated telemetry (gitignored)
│
├── artifacts/              # Model outputs (gitignored)
│   ├── isoforest.joblib
│   ├── metrics.json
│   ├── explanations_top.json
│   ├── aggregate_summaries.json
│   └── alerts.json
│
├── docs/
│   └── validation_report_sample.json
│
├── tests/
│   └── test_validation.py
│
├── requirements.txt
├── pytest.ini
└── README.md
```

---

## Outputs & Artifacts

Running the scoring pipeline produces operator-ready artifacts:

| File | Description |
|------|-------------|
| `artifacts/metrics.json` | Selected threshold and performance metrics (precision, recall, F1, ROC-AUC) |
| `artifacts/explanations_top.json` | Per-event feature attributions and sensor family breakdowns |
| `artifacts/aggregate_summaries.json` | Device-level and fleet-level anomaly summaries |
| `artifacts/alerts.json` | Operator-ready alerts with severity, root cause, and confidence |

These artifacts are designed for:
- Real-time dashboards
- REST APIs
- Incident management systems (PagerDuty, ServiceNow, etc.)
- Offline analysis and reporting
- Predictive maintenance workflows

---

## Setup Instructions

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Usage

### 1. Generate Telemetry

```bash
python -m itap.telemetry.run_generate
```

**Output:**
- `data/raw/telemetry_sample.csv` (gitignored)

### 2. Run Validation

```bash
python -m itap.validation.report
```

**Outputs:**
- Console summary
- `docs/validation_report_sample.json`

### 3. Ingest Data into SQL

```bash
python -m itap.storage.ingest
```

**Behavior:**
- First run inserts all rows
- Subsequent runs insert 0 rows (idempotent)

### 4. Train Anomaly Model

```bash
python -m itap.ml.run_train
```

**Outputs:**
- Trained Isolation Forest pipeline
- Saved to `artifacts/isoforest.joblib`

### 5. Score & Generate Alerts

```bash
python -m itap.ml.run_score
```

**Outputs:**
- Threshold sweep results
- Per-fault recall diagnostics
- Top anomalous events with explanations
- Device/fleet aggregation summaries
- Operator-ready alerts
- `artifacts/metrics.json`
- `artifacts/explanations_top.json`
- `artifacts/aggregate_summaries.json`
- `artifacts/alerts.json`

### 6. Run Tests

```bash
pytest -q
```

All tests should pass.

---

## Design Philosophy

**Key principles:**

1. **Operator-first, not model-first**
   - Outputs are designed for human operators, not just data scientists
   - Clear explanations over black-box predictions

2. **Explain before alert**
   - Every anomaly includes feature attribution
   - Sensor family grouping for domain-relevant insights

3. **Aggregate before escalate**
   - Move from individual events to device/fleet patterns
   - Reduce alert fatigue through intelligent summarization

4. **Deterministic rules layered on ML**
   - ML provides anomaly scores
   - Rules provide actionable root causes and severity

5. **Validation before storage**
   - Prevent garbage-in/garbage-out
   - Data quality checks at ingestion boundaries

6. **Idempotent ingestion**
   - Safe to re-run
   - Supports backfills and automation

7. **Time-aware modeling**
   - Prevent data leakage
   - Respect temporal causality

8. **Explicit feature engineering**
   - No hidden transformations
   - Fully deterministic and testable

---

## Current Maturity Level

✅ **Implemented:**
- Telemetry simulation with fault injection
- Schema validation and diagnostics
- Idempotent SQL ingestion pipeline
- Time-series feature engineering (60+ features)
- Unsupervised anomaly detection (Isolation Forest)
- Threshold optimization and evaluation
- Per-event explainability with sensor family attribution
- Fleet/device aggregation
- Rule-based alert generation with severity classification
- JSON artifact generation

🚧 **Future Enhancements:**
- Streaming inference pipeline
- Concept drift detection
- Alert deduplication and suppression
- REST API for real-time scoring
- Web dashboard (Streamlit / Dash)
- Auto-remediation hooks
- Multi-model ensemble (Autoencoder, LSTM-VAE)
- Forecasting (temperature, vibration trends)

---

## Example Output

### Console Output from `run_score.py`:

```
Threshold sweep results (sorted by recall then precision):
{'threshold': 0.1234, 'precision': 0.82, 'recall': 0.91, 'f1': 0.86, 'roc_auc': 0.94}

Selected metrics:
{
  "threshold": 0.1234,
  "precision": 0.82,
  "recall": 0.91,
  "f1": 0.86,
  "roc_auc": 0.94
}

Per-tag recall (on tagged rows only):
power_spike: recall=0.95, tp=19, fn=1
overheat: recall=0.88, tp=15, fn=2
bearing_wear: recall=0.92, tp=11, fn=1

Top 20 anomalous events (highest scores):
[DataFrame output]

Top contributing features (normalized %) for flagged anomalies:
- 2026-01-01 05:31:10 | DEV-0006 | RUN | tag=power_spike | score=0.185200 | pred=1
    Families: Voltage=24.7%, Temperature=24.6%, Current=20.2%
    voltage_v_trend: 5.9%
    voltage_v_mean: 5.9%

Fleet/Device Aggregations
- DEV-0006 | n=3 | avg_score=0.1765 | p95=0.1839 | Voltage=25.2%, Temperature=25.0%

ALERTS (operator-ready):
- CRITICAL | 2026-01-01 05:31:10 | DEV-0006 | RUN | score=0.1852
  cause=Power instability | conf=1.00 | Voltage=24.7%, Temperature=24.6%
  rule=power_instability_voltage_current
```

---

## Author

**Jose Santana**  
Entry-Level Software / Systems Engineer  
Focus: Data Engineering, ML Systems, Industrial Analytics

---

## License

MIT License
