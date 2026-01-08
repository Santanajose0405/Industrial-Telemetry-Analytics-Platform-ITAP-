"""
Validation report generator.

Loads a dataset, runs validation checks, and emits
a structured summary suitable for logging or diagnostics.
"""

from pathlib import Path
from typing import Dict

import pandas as pd

from itap.validation.validators import (
    validate_schema,
    missing_value_rates,
    range_checks,
)

def generate_validation_report(csv_path: str) -> Dict:
    df = pd.read_csv(csv_path)

    report = {
        "rows": int(len(df)),
        "schema": validate_schema(df),
        "missing_rates": missing_value_rates(df),
        "range_checks": range_checks(df),
    }

    return report

def main() -> None:
    csv_path = "data/raw/telemetry_sample.csv"
    report = generate_validation_report(csv_path)

    for section, values in report.items():
        print(f"\n[{section}]")
        print(values)

if __name__== "__main__":
    main()