"""
CSV -> SQL ingestion pipeline.

Designed to be:
- Idempotent (safe to re-run)
- Explicit about data transformations
- Compatible with validation layer
"""

from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import select

from itap.storage.database import ENGINE, SessionLocal
from itap.storage.models import Base, TelemetryRecord

def init_db() -> None:
    """ Create database tables if they do not exist. """
    Base.metadata.create_all(bind=ENGINE)

def ingest_csv(csv_path: str) -> int:
    """
    Ingest telemetry CSV into the database.

    Returns the number of rows inserted.
    """
    init_db()

    df = pd.read_csv(csv_path)

    # Normalize timestamp
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    
    inserted = 0
    with SessionLocal() as session:
        for _, row in df.iterrows():
            # Simple idempotency check: device_id + timestamp
            exists = session.execute(
                select(TelemetryRecord).where(
                    TelemetryRecord.device_id == row["device_id"],
                    TelemetryRecord.timestamp == row["timestamp"],
                )
            ).first()

            if exists:
                continue

            record = TelemetryRecord(
                timestamp=row["timestamp"],
                device_id=row["device_id"],
                state=row["state"],
                rpm=row["rpm"],
                temp_c=row["temp_c"],
                vibration_g=row["vibration_g"],
                current_a=row["current_a"],
                voltage_v=row["voltage_v"],
                error_code=row["error_code"],
                anomaly_tag=row["anomaly_tag"],
            )

            session.add(record)
            inserted += 1

        session.commit()

    return inserted

def main() -> None:
    csv_path = "data/raw/telemetry_sample.csv"
    rows = ingest_csv(csv_path)
    print(f"Ingested {rows} new rows into telemetry database.")

if __name__ == "__main__":
    main()
