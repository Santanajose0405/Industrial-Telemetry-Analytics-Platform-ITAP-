"""
Dataset validation utilities.

These checks are intentionally lightweight and deterministic.
They are designed to catch data quality issues early in the pipeline
before downstream modeling or storage.
"""
from typing import Dict, List

import pandas as pd


REQUIRED_COLUMNS: List[str] = [
    "timestamp",
    "device_id",
    "state",
    "rpm",
    "temp_c",
    "vibration_g",
    "current_a",
    "voltage_v",
    "error_code",
    "anomaly_tag",
 ]

def validate_schema(df: pd.DataFrame) -> Dict[str, bool]:
    """Ensure required columns are present."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    return {
        "schema_valid": len(missing) == 0,
        "missing_columns": missing,
    }

def missing_value_rates(df: pd.DataFrame) -> Dict[str, float]:
    """Compute NaN rate per column."""
    return {
        col: float(df[col].isna().mean())
        for col in df.columns
    }

def range_checks(df: pd.DataFrame) -> Dict[str, int]:
    """
    Basic sanity checks for numeric ranges.
    These are intentionally conservative.
    """
    issues = {}

    issues["rpm_negative"] = int((df["rpm"] < 0).sum())
    issues["temp_out_of_bounds"] = int(
        ((df["temp_c"] < -20) | (df["temp_c"] > 120)).sum()
    )
    issues["voltage_out_of_bounds"] = int(
        ((df["voltage_v"] < 20) | (df["voltage_v"] > 30)).sum()
    )

    return issues