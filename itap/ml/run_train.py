"""
Train the anomaly model from telemetry stored in SQL.

Operational note:
- This is an offline training job (batch).
- Week 4 can add scheduled runs / CI artifacts if desired.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import select

from itap.storage.database import SessionLocal
from itap.storage.models import TelemetryRecord
from itap.ml.features import build_rolling_features
from itap.ml.anomaly import train_anomaly_model, save_pipeline


def load_training_dataframe(limit: int | None = None) -> pd.DataFrame:
    """
    Load telemetry rows for training.

    We keep this simple: pull all rows (or a limit) ordered by time.
    For large-scale systems, we'd page or push down filters by time/device.
    """
    stmt = select(TelemetryRecord).order_by(TelemetryRecord.timestamp.asc())
    if limit is not None:
        stmt = stmt.limit(int(limit))

    with SessionLocal() as session:
        rows = session.execute(stmt).scalars().all()

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


def main() -> None:
    df = load_training_dataframe()
    if df.empty:
        raise SystemExit("No telemetry found in DB. Run ingestion first.")

    X, y = build_rolling_features(df, window=30)

    # Train primarily on "normal" rows to avoid learning injected fault patterns.
    X_train = X[y == 0]

    pipeline = train_anomaly_model(X_train, contamination=0.02)

    Path("artifacts").mkdir(parents=True, exist_ok=True)
    save_pipeline(pipeline, "artifacts/isoforest.joblib")

    print(f"Trained model on {len(X_train):,} normal rows. Saved to artifacts/isoforest.joblib")
    normal_rows = int((y == 0).sum())
    anomaly_rows = int((y == 1).sum())
    print(f"Label breakdown: normal={normal_rows:,}, anomalous={anomaly_rows:,}")

    if normal_rows == 0:
        raise SystemExit(
            "No normal rows available for training. "
            "Check anomaly_tag normalization or reduce fault injection rate."
        )

if __name__ == "__main__":
    main()
