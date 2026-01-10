# Industrial Telemetry Analytics Platform (ITAP)

A modular, Python-based industrial telemetry analytics platform that simulates, validates, ingests, stores, and analyzes time-series machine data.

This project demonstrates **real-world data engineering, time-series feature engineering, and ML system design** patterns commonly used in industrial IoT, manufacturing, and reliability engineering environments.

---

## Project Goals

- Simulate realistic industrial telemetry with controllable fault injection
- Validate and diagnose data quality issues before persistence or modeling
- Ingest time-series data into a SQL database using an idempotent pipeline
- Engineer meaningful time-series features from raw sensor signals
- Detect anomalous machine behavior using unsupervised learning
- Produce reproducible metrics and diagnostic artifacts

This project prioritizes **engineering realism, correctness, and explainability** over toy datasets or inflated metrics.

---

## Design Philosophy

- **Validation before storage** to prevent garbage-in/garbage-out
- **Idempotent ingestion** to support retries, automation, and backfills
- **Time-aware modeling** to avoid leakage
- **Explicit feature engineering** over opaque abstractions
- **Deterministic, testable code paths**
- Favor clarity and traceability over cleverness

---

## Architecture Overview

Telemetry Generator  
↓  
Validation & Diagnostics  
↓  
CSV Ingestion Pipeline  
↓  
SQL Storage (SQLite / PostgreSQL-ready)  
↓  
Time-Series Feature Engineering  
↓  
Unsupervised Anomaly Detection  
↓  
Evaluation & Diagnostics  

---

## Repository Structure

itap/

├── telemetry/ # Telemetry simulation & fault injection
\
├── validation/ # Schema, missing data, and range validation
\
├── storage/ # SQL models, database config, ingestion
\
├── ml/ # Feature engineering, training, scoring, evaluation
\
│ ├── features.py
\
│ ├── anomaly.py
\
│ ├── evaluate.py
\
│ ├── run_train.py
\
│ └── run_score.py
\
│
\
configs/
\
├── local.example.yaml
\
│
\
data/
\
├── raw/ # Generated telemetry (gitignored)
\
│
\
docs/
\
├── validation_report_sample.json
\
│
\
tests/
\
├── test_validation.py
\
│
\
requirements.txt
\
pytest.ini
\
README.md
\
yaml

---

## Features Implemented

### 1. Telemetry Simulation

- Multi-device time-series generation
- Configurable sampling frequency and duration
- Operating states (RUN, IDLE, MAINT)
- Fault injection:
  - Overheat drift
  - Bearing wear
  - Power spikes
  - Sensor dropouts
- Realistic temporal behavior (gradual vs abrupt faults)

---

### 2. Validation & Diagnostics

- Schema validation
- Missing value rate analysis
- Range and sanity checks
- Machine-readable validation reports
- Validation performed **before ingestion**

---

### 3. SQL Storage & Ingestion

- SQLAlchemy-based schema
- SQLite backend (PostgreSQL-compatible design)
- Timestamp + device indexing
- Idempotent ingestion (safe to re-run)
- Clear separation of models, ingestion, and queries

---

### 4. Time-Series Feature Engineering

Implemented explicitly in `itap/ml/features.py`:

- Rolling statistics (mean, std, min, max)
- Signal deltas and z-scores
- First differences (spike detection)
- Frequency-domain indicators (FFT energy, dominant frequency)
- Trend and seasonality decomposition
- Event-based counters:
  - Error streak length
  - Time since last error
  - State transition counts

All features are:
- Per-device
- Time-aligned
- Deterministic
- Leakage-safe

---

### 5. Machine Learning – Anomaly Detection

- Unsupervised Isolation Forest
- Trained only on *normal* operating data
- Outputs continuous anomaly scores
- Threshold selection via percentile sweep
- Label-aware evaluation for diagnostics only

---

### 6. Model Evaluation & Diagnostics

- Time-based train/test split
- Precision, recall, F1, ROC-AUC
- Per-fault-type recall breakdown
- Top-N anomalous event inspection
- Metrics persisted to `artifacts/metrics.json`

Metrics are intentionally realistic and reflect real-world class imbalance.

---

## Setup Instructions

### 1. Create and activate a virtual environment

python -m venv .venv
.venv\Scripts\activate

### 2. Install dependencies

pip install -r requirements.txt


## Usage

### Generate Telemetry

python -m itap.telemetry.run_generate

#### Output:

- data/raw/telemetry_sample.csv (gitignored)

### Run Validation

python -m itap.validation.report

##### Outputs:

- Console summary
- docs/validation_report_sample.json

### Ingest Data into SQL

python -m itap.storage.ingest

#### Behavior:

- First run inserts all rows
- Subsequent runs insert 0 rows (idempotent)

### Train Anomaly Model

python -m itap.ml.run_train

#### Outputs:

- Trained Isolation Forest model
- Saved to artifacts/isoforest.joblib

### Score & Evaluate Anomalies

python -m itap.ml.run_score

#### Outputs:

- Threshold sweep metrics
- Per-fault recall diagnostics
- Top anomalous events
- artifacts/metrics.json

### Run Tests

pytest -q

All tests should pass.

## Roadmap (Optional Extensions)

- Forecasting models (temperature, vibration, load)
- Concept drift detection
- Feature attribution / explainability
- CLI fault replay tools
- Dashboard visualization
- CI/CD automation

# Author
## Jose Santana
### Entry-Level Software / Systems Engineer
### Focus: Data Engineering, ML Systems, Industrial Analytics

License
MIT License