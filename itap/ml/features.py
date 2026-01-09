"""
Feature extraction for time-series telemetry.

Design intent:
- Convert raw telemetry into numeric features suitable for ML models
- Preserve per-device temporal structure (rolling windows)
- Keep transformations deterministic and reproducible

This module does not touch the database directly; it works on DataFrames.
"""

from __future__ import annotations

from typing import List, Tuple

import numpy as np
import pandas as pd


DEFAULT_SIGNALS = ["rpm", "temp_c", "vibration_g", "current_a", "voltage_v"]


def build_rolling_features(
    df: pd.DataFrame,
    signals: List[str] | None = None,
    window: int = 30,
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Build rolling-window features per device.

    Args:
        df: Raw telemetry with at least timestamp, device_id, and signal columns.
        signals: Numeric columns to featurize.
        window: Rolling window size in rows (not time-based). Conservative, simple baseline.

    Returns:
        X: Feature matrix (DataFrame) aligned to original rows that can be scored.
        y: Binary ground truth label derived from anomaly_tag (1=anomalous, 0=normal).

    Notes:
        - We intentionally keep the baseline simple: mean/std/min/max per signal.
        - Missing values are forward-filled per device, then remaining NaNs filled with column medians.
          This mirrors common telemetry handling where dropouts occur but signals recover.
    """
    if signals is None:
        signals = DEFAULT_SIGNALS

    df = df.copy()

    # Ensure consistent ordering for rolling calculations.
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.sort_values(["device_id", "timestamp"]).reset_index(drop=True)

    # Ground truth for evaluation: anomaly_tag is injected by the simulator.
    # anomaly_tag is considered "present" only if it contains a real, non-empty label.
    # CSV/SQL roundtrips may surface missing values as NaN or the literal string "nan".
    tag = df["anomaly_tag"].fillna("").astype(str).str.strip()
    tag = tag.replace({"nan": "", "None": "", "NULL": "", "null": ""})
    y = (tag != "").astype(int)

    # Handle missing sensor values in a device-aware way.
    df[signals] = (
        df.groupby("device_id")[signals]
        .apply(lambda g: g.ffill())
        .reset_index(level=0, drop=True)
    )

    # Fill any remaining NaNs with global medians (stable default for baseline).
    medians = df[signals].median(numeric_only=True)
    df[signals] = df[signals].fillna(medians)

    feature_frames = []
    for sig in signals:
        # Rolling features per device. We use min_periods to avoid dropping early rows.
        grp = df.groupby("device_id")[sig]

        feature_frames.append(grp.rolling(window=window, min_periods=max(5, window // 5)).mean().rename(f"{sig}_mean"))
        feature_frames.append(grp.rolling(window=window, min_periods=max(5, window // 5)).std().rename(f"{sig}_std"))
        feature_frames.append(grp.rolling(window=window, min_periods=max(5, window // 5)).min().rename(f"{sig}_min"))
        feature_frames.append(grp.rolling(window=window, min_periods=max(5, window // 5)).max().rename(f"{sig}_max"))

    X = pd.concat(feature_frames, axis=1).reset_index(level=0, drop=True)

    # std can be NaN when min_periods not met; fill with 0 as "no variability observed yet".
    X = X.replace([np.inf, -np.inf], np.nan).fillna(0.0)

    return X, y
