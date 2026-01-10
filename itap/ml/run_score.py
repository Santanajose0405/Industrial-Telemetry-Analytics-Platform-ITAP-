from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

import numpy as np
import pandas as pd

from itap.ml.anomaly import load_pipeline
from itap.ml.evaluate import threshold_sweep, per_tag_recall
from itap.ml.features import build_rolling_features

# Explainability
from itap.ml.explain import build_explain_df, print_operator_explanations

# Aggregation + alerts
from itap.ml.aggregate import (
    aggregate_explanations,
    print_aggregate_summaries,
    summaries_to_json,
)
from itap.ml.alerts import (
    build_alert_event_from_row,
    print_alerts,
    alerts_to_json,
)

from itap.storage.database import SessionLocal
from itap.storage.models import TelemetryRecord


# -----------------------------
# Configuration
# -----------------------------
MODEL_PATH = "artifacts/isoforest.joblib"
WINDOW = 30
TOP_N = 20
ARTIFACT_DIR = Path("artifacts")


def load_dataframe() -> pd.DataFrame:
    """
    Load telemetry from SQL into a DataFrame.

    We intentionally keep this as a thin adapter:
    - DB layer returns ORM models
    - This function returns a clean, explicit DataFrame schema for ML
    """
    with SessionLocal() as session:
        rows = session.query(TelemetryRecord).order_by(TelemetryRecord.timestamp.asc()).all()

    data = [
        {
            "timestamp": r.timestamp,
            "device_id": r.device_id,
            "state": r.state,
            "rpm": r.rpm,
            "temp_c": r.temp_c,
            "vibration_g": r.vibration_g,
            "current_a": r.current_a,
            "voltage_v": r.voltage_v,
            "error_code": r.error_code,
            "anomaly_tag": r.anomaly_tag,
        }
        for r in rows
    ]
    return pd.DataFrame(data)


def _select_best_from_sweep(
    sweep_out: Union[List[Dict[str, Any]], Tuple[List[Dict[str, Any]], Dict[str, Any]]]
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Support either threshold_sweep return style:

      A) threshold_sweep(...) -> list[dict]
      B) threshold_sweep(...) -> (list[dict], best_dict)

    Returns:
      (sweep_list, best_dict)
    """
    if isinstance(sweep_out, tuple):
        sweep, best = sweep_out
    else:
        sweep = sweep_out
        best = sweep[0] if len(sweep) > 0 else None

    # Defensive: some versions may accidentally return best as a list
    if isinstance(best, list):
        best = best[0] if len(best) > 0 else None

    if not isinstance(sweep, list) or len(sweep) == 0:
        raise SystemExit("threshold_sweep returned no results; cannot select a threshold.")
    if not isinstance(best, dict):
        raise SystemExit("threshold_sweep did not return a valid best result dict.")
    if "threshold" not in best:
        raise SystemExit("Best sweep result missing required key: 'threshold'.")

    return sweep, best


def main() -> None:
    """
    Offline scoring job:

    1) Load telemetry from DB
    2) Build rolling window features
    3) Load trained pipeline and score each row
    4) Select threshold (via sweep)
    5) Print operator-ready output:
       - top anomalies
       - per-row feature attribution
       - aggregate summaries
       - alert events
    6) Write JSON artifacts for reproducibility / portfolio review
    """
    if not Path(MODEL_PATH).exists():
        raise SystemExit("Model not found. Run: python -m itap.ml.run_train")

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    # -----------------------------
    # Load + feature engineering
    # -----------------------------
    df = load_dataframe()
    if df.empty:
        raise SystemExit("No telemetry data found in DB. Run ingestion first.")

    # X aligns to df row order AFTER feature builder sorts by (device_id, timestamp).
    # We rely on X.index for safe alignment back to the raw df.
    X, y = build_rolling_features(df, window=WINDOW)

    # -----------------------------
    # Load model + score
    # -----------------------------
    pipeline = load_pipeline(MODEL_PATH)

    # NOTE:
    # IsolationForest returns a decision score; “more anomalous” depends on your convention.
    # In your current pipeline.score implementation, you're using a score where higher => more anomalous.
    scores = pipeline.score(X)

    # -----------------------------
    # Threshold sweep
    # -----------------------------
    sweep_out = threshold_sweep(y, scores)
    sweep, best = _select_best_from_sweep(sweep_out)

    print("\nThreshold sweep results (sorted by recall then precision):")
    for r in sweep:
        print(r)

    print("\nSelected metrics:")
    print(json.dumps(best, indent=2))

    threshold = float(best["threshold"])
    preds = (scores >= threshold).astype(int)

    # -----------------------------
    # Attach results to dataframe
    # -----------------------------
    # Use X.index to ensure alignment to the feature-engineered row order.
    scored = df.loc[X.index].copy()
    scored["score"] = scores
    scored["pred"] = preds

    # -----------------------------
    # Per-tag recall
    # -----------------------------
    # This should summarize recall on rows where anomaly_tag was injected (tagged faults).
    print("\nPer-tag recall (on tagged rows only):")
    per_tag_recall(scored)

    # -----------------------------
    # Top anomalies (for operator review)
    # -----------------------------
    top = scored.sort_values("score", ascending=False).head(TOP_N)

    print(f"\nTop {TOP_N} anomalous events (highest scores):")
    print(top)

    # -----------------------------
    # Explainability (per-row)
    # -----------------------------
    # IMPORTANT:
    # Your current build_explain_df signature is:
    #   build_explain_df(*, pipeline, X_test, top_rows, ...)
    # so we must pass X_test=... and top_rows=...
    df_explain = build_explain_df(
        pipeline=pipeline,
        X_test=X,
        top_rows=top,
        score_col="score",
        pred_col="pred",
        tag_col="anomaly_tag",
        top_k_features=5,
    )

    # Print compact operator output (top families + top features per event)
    print_operator_explanations(
        df_explain,
        top_k_families=3,
        top_k_features=5,
    )

    # Persist explain output for portfolio review
    df_explain.to_json(
        ARTIFACT_DIR / "explanations_top.json",
        orient="records",
        indent=2,
    )

    # -----------------------------
    # Aggregation (fleet / device / tag summaries)
    # -----------------------------
    # Design intent: move from “row-level spikes” to operator-friendly summaries.
    summaries = aggregate_explanations(
        rows=df_explain,
        family_totals_col="family_totals",
        group_by="device_id",
        score_col="score",
        top_k_families=5,
    )

    print_aggregate_summaries(
        title="Fleet/Device Aggregations",
        summaries=summaries,
        top_n=10
    )

    with open(ARTIFACT_DIR / "aggregate_summaries.json", "w", encoding="utf-8") as f:
        json.dump(summaries_to_json(summaries), f, indent=2)

    # -----------------------------
    # Alerts (rule-ready output)
    # -----------------------------
    # For now: create one AlertEvent per explained row.
    # Next maturity step: rule evaluation (burst rules, device streaks, family dominance, etc.)
    alerts = [
        build_alert_event_from_row(
            row=r,
            families=r.get("families_sorted", []),
            top_features=r.get("top_features", []),
            score_col="score",
            tag_col="anomaly_tag",
        )
        for _, r in df_explain.iterrows()
    ]

    print_alerts(alerts)

    with open(ARTIFACT_DIR / "alerts.json", "w", encoding="utf-8") as f:
        json.dump(alerts_to_json(alerts), f, indent=2)

    # -----------------------------
    # Persist metrics
    # -----------------------------
    with open(ARTIFACT_DIR / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(best, f, indent=2)

    print("\nWrote artifacts:")
    print(" - artifacts/metrics.json")
    print(" - artifacts/explanations_top.json")
    print(" - artifacts/aggregate_summaries.json")
    print(" - artifacts/alerts.json")


if __name__ == "__main__":
    main()
