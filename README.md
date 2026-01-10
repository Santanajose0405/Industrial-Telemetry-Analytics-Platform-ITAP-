# Industrial Telemetry Analytics Platform (ITAP)

A modular, Python-based telemetry analytics platform designed to simulate, validate, ingest, and store industrial time-series data.  
This project demonstrates real-world data engineering, systems integration, and analytics workflows commonly used in IoT and industrial environments.

---

## Project Goals

- Simulate realistic industrial telemetry with configurable fault injection
- Validate and diagnose data quality issues before storage or modeling
- Ingest time-series telemetry into a SQL database using an idempotent pipeline
- Provide a clean foundation for downstream machine learning and analytics

This project is intentionally **data-driven, testable, and production-oriented**.

---

## Design Notes
 - Validation is performed before storage to prevent corrupt or misleading data
 - SQL ingestion is idempotent to support retries and automation
- Metrics are derived from persisted data to reflect real operational state
- SQLite is used for local development; schema is PostgreSQL-compatible

---

## Architecture Overview

Telemetry Generator
↓
Validation & Diagnostics
↓
CSV Ingestion Pipeline
↓
SQL Storage (SQLite)
↓
(Week 3) ML / Anomaly Detection

yaml
Copy code

---

## Repository Structure

itap/
├── telemetry/ # Telemetry simulation & fault injection
├── validation/ # Schema, missing data, and range validation
├── storage/ # SQL models, database config, ingestion
│
configs/
├── local.example.yaml # Example runtime configuration
│
data/
├── raw/ # Generated telemetry (gitignored)
│ └── .gitkeep
│
docs/
├── validation_report_sample.json
│
tests/
├── test_validation.py # Automated validation tests
│
requirements.txt
pytest.ini
README.md

markdown
Copy code

---

## Features Implemented

### Telemetry Simulation
- Multi-device time-series generation
- Configurable sampling frequency and duration
- Seasonal signal behavior
- Fault injection:
  - Overheat drift
  - Bearing wear
  - Sensor dropout
  - Power spikes

### Validation & Diagnostics
- Schema validation
- Missing value rate analysis
- Range and sanity checks
- Machine-readable validation report artifact

### SQL Storage & Ingestion
- SQLAlchemy-based schema
- SQLite backend (PostgreSQL-ready design)
- Timestamp + device indexing
- Idempotent ingestion (safe to re-run)

### Testing & Quality
- Pytest-based automated tests
- Deterministic, in-memory test data
- Clean package structure
- IDE and artifact hygiene

---

## Setup Instructions

### 1. Create and activate a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\activate
2. Install dependencies
powershell
Copy code
pip install -r requirements.txt
Usage
Generate Telemetry Data
powershell
Copy code
python -m itap.telemetry.run_generate
Output:

data/raw/telemetry_sample.csv (not committed)

Run Validation Report
powershell
Copy code
python -m itap.validation.report
Outputs:

Console summary

docs/validation_report_sample.json

Ingest Data into SQL Database
powershell
Copy code
python -m itap.storage.ingest
Expected behavior:

First run inserts all rows

Subsequent runs insert 0 rows (idempotent)

Run Tests
powershell
Copy code
pytest -q
All tests should pass.

Design Decisions
Config-driven execution for flexibility and reproducibility

Validation before storage to prevent garbage-in/garbage-out

Idempotent ingestion to support retries and automation

SQLite for local dev, with PostgreSQL-compatible patterns

Explicit, readable code over clever abstractions

Roadmap
Week 3: Anomaly detection & time-series modeling

Week 4: Dashboards, ML evaluation, and polish

Optional: Cloud deployment and CI enhancements

Author
Jose Santana
Entry-Level Software / Systems Engineer
Focus areas: Data Engineering, ML Systems, Industrial Analytics

License
MIT License