"""
Score telemetry using a trained anomaly model and report evaluation metrics.

This is an offline scoring job that helps you iterate on:
- feature window sizes
- contamination settings
- score thresholds

Key design notes:
- We evaluate on a time-based holdout (later timestamps) to reduce leakage.
- We sweep score thresholds (percentiles) to understand precision/recall tradeoffs.
- We print the highest-scoring events to support troubleshooting and model iteration.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from itap.ml.anomaly import load_pipeline
from itap.ml.evaluate import evaluate_scores
from itap.ml.features import build_rolling_features
from itap.ml.run_train import load_training_dataframe


def main() -> None:
    model_path = Path("artifacts/isoforest.joblib")
    if not model_path.exists():
        raise SystemExit("Model not found. Run: python -m itap.ml.run_train")

    df = load_training_dataframe()
    if df.empty:
        raise SystemExit("No telemetry found in DB. Run ingestion first.")

    # Time-aware split (prevents leakage): train on earlier data, evaluate on later data.
    df = df.sort_values("timestamp").reset_index(drop=True)
    split_idx = int(len(df) * 0.70)

    # We evaluate on the later slice to simulate "future" scoring.
    df_test = df.iloc[split_idx:].copy()

    # Optional: focus on production-like behavior; MAINT often looks anomalous by design.
    df_test = df_test[df_test["state"].isin(["RUN", "IDLE"])].copy()

    # Build features for the test slice.
    X_test, y_test = build_rolling_features(df_test, window=30)

    pipeline = load_pipeline(str(model_path))
    try:
        scores = pipeline.score(X_test)
    except ValueError as e:
        raise SystemExit(
            "Feature mismatch between trained model and current feature set.\n"
            "Re-train the model with: python -m itap.ml.run_train\n\n"
            f"Original error: {e}"
        )

    # Threshold sweep: percentile thresholds approximate "flag top X% as anomalous".
    # Lower percentile => more alerts (higher recall, lower precision).
    candidates = np.percentile(scores, [85, 88, 90, 95, 97, 98, 99])

    results = []
    for t in candidates:
        m = evaluate_scores(y_test.to_numpy(), scores, threshold=float(t))
        results.append(m)

    # Selection policy: prioritize recall, break ties with precision.
    # In real systems, this is driven by business cost (missed faults vs false alarms).
    results = sorted(results, key=lambda x: (x["recall"], x["precision"]), reverse=True)
    best = results[0]

    print("\nThreshold sweep results (sorted by recall then precision):")
    for r in results:
        print(r)

    print("\nSelected metrics:")
    print(json.dumps(best, indent=2))

    # Use the selected threshold to generate a binary prediction vector (0/1).
    threshold = float(best["threshold"])
    pred = (scores >= threshold).astype(int)

    # Per-tag recall: which injected failure modes are we detecting?
    tags = df_test["anomaly_tag"].fillna("").astype(str).str.strip()
    tags = tags.replace({"nan": "", "None": "", "NULL": "", "null": ""})

    print("\nPer-tag recall (on tagged rows only):")
    for t in sorted(set(tags) - {""}):
        mask = (tags == t).to_numpy()
        tp = int(((y_test.to_numpy() ==1) & (pred == 1) & mask).sum())
        fn = int(((y_test.to_numpy() == 1) & (pred == 0) & mask).sum())
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        print(f"- {t}: recall={rec:.3f} (tp={tp}, fn={fn})")

    # Print top-N highest-scoring rows to support investigation ("what did it flag?").
    top_idx = np.argsort(scores)[-20:][::-1]
    top_anomalies = df_test.iloc[top_idx].copy()
    top_anomalies["score"] = scores[top_idx]
    top_anomalies["pred"] = pred[top_idx]

    cols = [
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
        "score",
        "pred",
    ]

    print("\nTop 20 anomalous events (highest scores):")
    print(top_anomalies[cols])

    # Persist the chosen metrics for tracking over iterations.
    Path("artifacts").mkdir(parents=True, exist_ok=True)
    with open("artifacts/metrics.json", "w", encoding="utf-8") as f:
        json.dump(best, f, indent=2)

    print("\nWrote artifacts/metrics.json")


if __name__ == "__main__":
    main()
