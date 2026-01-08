"""
Validation report generator.

Loads a dataset, runs validation checks, prints a structured summary,
and writes a JSON artifact to docs/ for portfolio visibility.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict
import json

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

    # Print to console (useful for local diagnostics)
    for section, values in report.items():
        print(f"\n[{section}]")
        print(values)

    # Persist a reviewer-friendly artifact
    out_path = Path("docs") / "validation_report_sample.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\nWrote validation artifact: {out_path}")


if __name__ == "__main__":
    main()
