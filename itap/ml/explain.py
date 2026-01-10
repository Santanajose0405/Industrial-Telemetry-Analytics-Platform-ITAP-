from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

# Keep this list in sync with DEFAULT_SIGNALS in features.py.
SIGNAL_PREFIXES = ["rpm", "temp_c", "vibration_g", "current_a", "voltage_v"]


def sensor_family(feature_name: str, signal_prefixes: List[str] | None = None) -> str:
    """
    Map a feature name -> operator-friendly sensor family.

    Examples:
      - voltage_v_mean          -> Voltage
      - temp_c_trend            -> Temperature
      - vibration_g_fft_band_3  -> Vibration
      - error_code_streak       -> Error/Flags
      - state_transition_count  -> State
    """
    if signal_prefixes is None:
        signal_prefixes = SIGNAL_PREFIXES

    # Prefer longest-prefix matching to avoid accidental partial matches.
    for sig in sorted(signal_prefixes, key=len, reverse=True):
        if feature_name.startswith(sig + "_"):
            return {
                "rpm": "RPM",
                "temp_c": "Temperature",
                "vibration_g": "Vibration",
                "current_a": "Current",
                "voltage_v": "Voltage",
            }.get(sig, sig)

    lowered = feature_name.lower()
    if lowered.startswith("error") or "error_code" in lowered or "flag" in lowered:
        return "Error/Flags"
    if lowered.startswith("state") or "transition" in lowered:
        return "State"
    if lowered.startswith("time") or lowered.startswith("ts_") or "timestamp" in lowered:
        return "Time"

    return "Other"


def top_contributions_for_row(
    z_row: np.ndarray,
    feature_names: List[str],
    top_k_features: int = 5,
) -> Tuple[List[Tuple[str, float]], Dict[str, float]]:
    """
    Compute normalized per-row contributions from a standardized feature row.

    Args:
      z_row: 1D array of standardized feature values (after scaler.transform).
      feature_names: list of feature names aligned with z_row indices.
      top_k_features: number of top individual features to return.

    Returns:
      top_features: list of (feature_name, percent_contribution) sorted desc.
      family_percents: dict {family: percent_contribution}.

    Notes:
      - Uses |z| as a simple, model-agnostic proxy for "what pushed this row away from normal".
      - Normalization makes explanations comparable across events.
    """
    z_row = np.asarray(z_row, dtype=float)
    abs_z = np.abs(z_row)

    # Guard against NaNs/Infs from upstream transformations
    abs_z = np.where(np.isfinite(abs_z), abs_z, 0.0)

    total = float(abs_z.sum())
    if total <= 0.0:
        return [], {}

    perc = abs_z / total  # sums to 1.0

    # Top individual features
    idx = np.argsort(perc)[::-1]
    top_idx = idx[:top_k_features]
    top_features = [(feature_names[i], float(perc[i] * 100.0)) for i in top_idx]

    # Group by sensor family
    family_totals: Dict[str, float] = {}
    for i, p in enumerate(perc):
        fam = sensor_family(feature_names[i])
        family_totals[fam] = family_totals.get(fam, 0.0) + float(p * 100.0)

    return top_features, family_totals


def build_explain_df(
    *,
    pipeline,
    X_test: pd.DataFrame,
    top_rows: pd.DataFrame,
    score_col: str = "score",
    pred_col: str = "pred",
    tag_col: str = "anomaly_tag",
    top_k_features: int = 5,
) -> pd.DataFrame:
    """
    Build a DataFrame of explainability artifacts for flagged rows.

    Requirements:
      - pipeline.scaler must be fitted and compatible with X_test columns.
      - top_rows must be aligned to the same row order as X_test (i.e., same index space).
        If you pass top_rows=top20.reset_index(drop=True), then X_test must also be reset_index(drop=True).

    Output columns:
      row_idx, timestamp, device_id, state, anomaly_tag, score, pred,
      top_features, family_totals, families_sorted
    """
    if top_rows is None or top_rows.empty:
        return pd.DataFrame()

    # Ensure deterministic ordering of columns for scaler.transform
    feature_names = list(X_test.columns)

    # Transform once for efficiency
    Z = pipeline.scaler.transform(X_test)  # shape [n_rows, n_features]

    records = []
    for row_idx, row in top_rows.iterrows():
        # Only explain flagged rows
        if int(row.get(pred_col, 0)) != 1:
            continue

        if row_idx < 0 or row_idx >= Z.shape[0]:
            # Defensive: skip if indices don't align
            continue

        top_feats, fam_totals = top_contributions_for_row(
            Z[row_idx],
            feature_names=feature_names,
            top_k_features=top_k_features,
        )
        fam_sorted = sorted(fam_totals.items(), key=lambda kv: kv[1], reverse=True)

        tag = row.get(tag_col, "")
        tag = "(unlabeled)" if (pd.isna(tag) or str(tag).strip() == "") else str(tag).strip()

        records.append(
            {
                "row_idx": int(row_idx),
                "timestamp": row.get("timestamp", ""),
                "device_id": row.get("device_id", ""),
                "state": row.get("state", ""),
                "anomaly_tag": tag,
                "score": float(row.get(score_col, 0.0)),
                "pred": int(row.get(pred_col, 0)),
                "top_features": top_feats,
                "family_totals": dict(fam_totals),
                "families_sorted": fam_sorted,
            }
        )

    return pd.DataFrame(records)


def print_operator_explanations(
    df_explain: pd.DataFrame,
    top_k_families: int = 3,
    top_k_features: int = 5,
) -> None:
    """
    Print operator-ready explanations for each row in df_explain.
    """
    print("\nTop contributing features (normalized %) for flagged anomalies:")
    print("(Per-row |z|-attribution with sensor-family grouping)\n")

    if df_explain is None or df_explain.empty:
        print("(no flagged rows to explain)")
        return

    for _, r in df_explain.iterrows():
        ts = r.get("timestamp", "")
        dev = r.get("device_id", "")
        state = r.get("state", "")
        tag = r.get("anomaly_tag", "(unlabeled)")
        score = float(r.get("score", 0.0))
        pred = int(r.get("pred", 0))

        print(f"- {ts} | {dev} | {state} | tag={tag} | score={score:.6f} | pred={pred}")

        fams = r.get("families_sorted", []) or []
        if fams:
            fam_str = ", ".join([f"{k}={v:.1f}%" for k, v in fams[:top_k_families]])
            print(f"    Families: {fam_str}")

        feats = r.get("top_features", []) or []
        for fname, pct in feats[:top_k_features]:
            print(f"    {fname}: {pct:.1f}%")
        print()
