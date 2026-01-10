"""
Feature extraction for time-series telemetry.

Design intent:
- Convert raw telemetry into numeric features suitable for ML models
- Preserve per-device temporal structure (rolling windows)
- Keep transformations deterministic and reproducible

We intentionally avoid "model magic" here; this module focuses on making
real-world telemetry usable for ML by creating stable, explainable features.

Key ideas:
- Rolling statistics per device (mean/std/min/max)
- Deviation features (delta, z-score) capture how "unusual" a point is
- Trend/seasonality (decomposition-lite) using rolling trend + residuals + phase bins
- Frequency-domain indicators (FFT energy + dominant frequency bin)
- Event-based counters (error streaks, state transitions, time since events)

This module does not touch the database directly; it works on DataFrames.
"""

from __future__ import annotations

from typing import Callable, List, Tuple

import numpy as np
import pandas as pd

DEFAULT_SIGNALS = ["rpm", "temp_c", "vibration_g", "current_a", "voltage_v"]


# -----------------------------
# Helpers
# -----------------------------

def _infer_sample_step_seconds(df: pd.DataFrame) -> int:
    """
    Infer an approximate sampling step in seconds.

    We use the median delta between consecutive timestamps across the whole DF.
    This is a pragmatic default for demo/portfolio work where sample rates are consistent.

    Returns:
        step_s: integer seconds, min 1
    """
    ts = pd.to_datetime(df["timestamp"], errors="coerce")
    deltas = ts.sort_values().diff().dt.total_seconds().dropna()

    if deltas.empty:
        return 1

    step = int(max(1, round(float(deltas.median()))))
    return step


def _streak_lengths(flag_series: pd.Series) -> pd.Series:
    """
    Convert a boolean series into "current streak length" at each row.

    Example:
        F F T T T F T
        0 0 1 2 3 0 1

    This is used for "error streaks" and similar event streak features.
    """
    flag = flag_series.fillna(False).astype(bool).to_numpy()

    out = np.zeros(len(flag), dtype=np.int32)
    streak = 0
    for i, v in enumerate(flag):
        if v:
            streak += 1
        else:
            streak = 0
        out[i] = streak

    return pd.Series(out, index=flag_series.index)


def _fft_energy(x: np.ndarray) -> float:
    """
    Simple FFT-based energy measure.
    - Removes DC component (subtract mean)
    - Computes rFFT magnitude and returns total spectral energy

    This is a compact proxy for "how much periodic / oscillatory content"
    is present in the recent window.
    """
    x = x.astype(float)
    x = x - np.mean(x)
    spec = np.fft.rfft(x)
    mag2 = (np.abs(spec) ** 2)
    return float(np.sum(mag2))


def _fft_dom_bin(x: np.ndarray) -> float:
    """
    Dominant frequency bin index (excluding the DC bin 0).

    Returns:
        float(bin_index) so pandas rolling.apply can store it.
    """
    x = x.astype(float)
    x = x - np.mean(x)
    spec = np.fft.rfft(x)
    mag = np.abs(spec)

    # Exclude DC to avoid "dominant = 0" when signal is steady.
    if len(mag) <= 1:
        return 0.0

    dom = int(np.argmax(mag[1:]) + 1)
    return float(dom)


# -----------------------------
# Main feature builder
# -----------------------------

def build_rolling_features(
    df: pd.DataFrame,
    signals: List[str] | None = None,
    window: int = 30,
    seasonal_period_s: int = 600,
    fft_window: int | None = None,
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Build rolling-window features per device.

    Args:
        df: Raw telemetry with at least timestamp, device_id, and signal columns.
        signals: Numeric columns to featurize.
        window: Rolling window size in rows (not time-based). Conservative baseline.
        seasonal_period_s: "Expected cycle length" in seconds for phase binning (decomposition-lite).
                          Example: 600s = 10 minutes.
        fft_window: Optional FFT window size. If None, defaults to `window`.

    Returns:
        X: Feature matrix (DataFrame) aligned to original rows that can be scored.
        y: Binary ground truth label derived from anomaly_tag (1=anomalous, 0=normal).

    Notes:
        - Missing values are forward-filled per device, then remaining NaNs filled with column medians.
        - All groupby+rolling outputs are flattened to align with df's flat row index.
    """
    if signals is None:
        signals = DEFAULT_SIGNALS

    if fft_window is None:
        fft_window = window

    df = df.copy()

    # Ensure consistent ordering for rolling calculations.
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.sort_values(["device_id", "timestamp"]).reset_index(drop=True)

    eps = 1e-6  # prevents division by zero for early/flat windows

    # Ground truth for evaluation:
    # anomaly_tag is injected by the simulator. CSV/SQL roundtrips may surface
    # missing as NaN or literal strings "nan"/"None"/etc.
    tag = df.get("anomaly_tag", "").fillna("").astype(str).str.strip()
    tag = tag.replace({"nan": "", "None": "", "NULL": "", "null": ""})
    y = (tag != "").astype(int)

    # Handle missing sensor values in a device-aware way.
    # Forward-fill within each device (telemetry dropouts are common).
    df[signals] = (
        df.groupby("device_id")[signals]
        .apply(lambda g: g.ffill())
        .reset_index(level=0, drop=True)
    )

    # Fill any remaining NaNs with global medians (stable baseline default).
    medians = df[signals].median(numeric_only=True)
    df[signals] = df[signals].fillna(medians)

    # -----------------------------
    # Trend / seasonality features (decomposition-lite)
    # -----------------------------
    # Instead of full STL decomposition, we:
    # - Create a rolling trend estimate (rolling mean)
    # - Create residual features (value - trend)
    # - Add a phase bin within an assumed period to help capture cyclical behavior
    step_s = _infer_sample_step_seconds(df)
    bins_per_period = max(1, int(round(seasonal_period_s / max(1, step_s))))

    if df["timestamp"].notna().any():
        # datetime64[ns] -> int64 nanoseconds -> seconds (no deprecated .view usage)
        ts_s = (df["timestamp"].astype("int64") // 1_000_000_000).astype("int64")

        phase_bin = (ts_s % seasonal_period_s) // max(1, step_s)
        phase_bin = phase_bin.clip(lower=0, upper=bins_per_period - 1)
    else:
        phase_bin = pd.Series(0, index=df.index)

    df["_phase_bin"] = phase_bin.astype(int)

    # Optional: encode phase as sin/cos to avoid ordinal artifacts
    phase_angle = 2.0 * np.pi * (df["_phase_bin"] / max(1, bins_per_period))
    phase_sin = np.sin(phase_angle).astype(float)
    phase_cos = np.cos(phase_angle).astype(float)

    # -----------------------------
    # Feature construction
    # -----------------------------
    feature_frames: List[pd.Series | pd.DataFrame] = []

    # Global time/seasonality encodings (same for all devices)
    feature_frames.append(pd.Series(phase_sin, index=df.index, name="phase_sin"))
    feature_frames.append(pd.Series(phase_cos, index=df.index, name="phase_cos"))

    # Rolling params chosen to avoid dropping early rows while still being meaningful.
    minp = max(5, window // 5)
    fft_minp = max(8, fft_window // 3)  # FFT is less meaningful with too few points

    for sig in signals:
        # Groupby series for per-device rolling computations
        grp = df.groupby("device_id")[sig]

        # Rolling container (MultiIndex output: (device_id, row_index))
        r = grp.rolling(window=window, min_periods=minp)

        # Basic rolling stats (flatten the MultiIndex to match df row index)
        feature_frames.append(r.mean().reset_index(level=0, drop=True).rename(f"{sig}_mean"))
        feature_frames.append(r.std().reset_index(level=0, drop=True).rename(f"{sig}_std"))
        feature_frames.append(r.min().reset_index(level=0, drop=True).rename(f"{sig}_min"))
        feature_frames.append(r.max().reset_index(level=0, drop=True).rename(f"{sig}_max"))

        # Trend estimate and residual (decomposition-lite)
        trend = r.mean().reset_index(level=0, drop=True)
        cur = df[sig]
        resid = (cur - trend).rename(f"{sig}_resid")
        feature_frames.append(trend.rename(f"{sig}_trend"))
        feature_frames.append(resid)

        # Deviation features
        rolling_mean = trend
        rolling_std = r.std().reset_index(level=0, drop=True)

        feature_frames.append((cur - rolling_mean).rename(f"{sig}_delta"))
        feature_frames.append(((cur - rolling_mean) / (rolling_std + eps)).rename(f"{sig}_zscore"))

        # First difference per device (flatten index)
        feature_frames.append(grp.diff().reset_index(level=0, drop=True).rename(f"{sig}_diff"))

        # -----------------------------
        # Frequency-domain indicators (FFT)
        # -----------------------------
        # FFT computed on recent window per device.
        # This is heavier than rolling stats but still feasible at this scale and valuable for portfolio work.
        rf = grp.rolling(window=fft_window, min_periods=fft_minp)

        fft_e = rf.apply(_fft_energy, raw=True).reset_index(level=0, drop=True).rename(f"{sig}_fft_energy")
        fft_dom = rf.apply(_fft_dom_bin, raw=True).reset_index(level=0, drop=True).rename(f"{sig}_fft_dom_bin")

        feature_frames.append(fft_e)
        feature_frames.append(fft_dom)

    # -----------------------------
    # Event-based counters
    # -----------------------------
    # Errors: streak length + time since last error
    err_active = df.get("error_code", 0).fillna(0).astype(int).ne(0)

    error_streak = (
        err_active.groupby(df["device_id"])
        .apply(_streak_lengths)
        .reset_index(level=0, drop=True)
        .rename("error_streak")
    )
    feature_frames.append(error_streak)

    last_err_ts = df["timestamp"].where(err_active)
    last_err_ts = last_err_ts.groupby(df["device_id"]).ffill()

    time_since_err = (df["timestamp"] - last_err_ts).dt.total_seconds()
    time_since_err = time_since_err.fillna(1e9).clip(lower=0).rename("time_since_error_s")
    feature_frames.append(time_since_err)

    # State transitions: 1 when state changes vs previous row (per device), else 0
    if "state" in df.columns:
        state = df["state"].fillna("").astype(str)

        prev_state = state.groupby(df["device_id"]).shift(1)
        state_change = (state != prev_state).fillna(False).astype(int).rename("state_change")

        # Rolling count of state changes in the last window (per device)
        sc_grp = state_change.groupby(df["device_id"])
        sc_roll = (
            sc_grp.rolling(window=window, min_periods=minp)
            .sum()
            .reset_index(level=0, drop=True)
            .rename("state_change_count")
        )

        feature_frames.append(state_change)
        feature_frames.append(sc_roll)

        # Time since last state change (seconds)
        # Mark timestamp where state changed, ffill within device, subtract current.
        last_change_ts = df["timestamp"].where(state_change.astype(bool))
        last_change_ts = last_change_ts.groupby(df["device_id"]).ffill()

        time_since_change = (df["timestamp"] - last_change_ts).dt.total_seconds()
        time_since_change = time_since_change.fillna(1e9).clip(lower=0).rename("time_since_state_change_s")
        feature_frames.append(time_since_change)

    # -----------------------------
    # Assemble feature matrix
    # -----------------------------
    # Everything in feature_frames must align on df.index (flat Index).
    X = pd.concat(feature_frames, axis=1)

    # Replace infs and fill NaNs.
    # NaNs are expected early in rolling windows and in std calculations.
    X = X.replace([np.inf, -np.inf], np.nan).fillna(0.0)

    return X, y
