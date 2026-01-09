"""
Query utilities for telemetry data.

This module provides a small data access layer (DAL) so downstream
code does not need to write raw SQLAlchemy queries.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import pandas as pd
from sqlalchemy import select

from itap.storage import database
from itap.storage.database import SessionLocal
from itap.storage.models import TelemetryRecord

def fetch_device_window(
    device_id: str,
    start: datetime,
    end: datetime,
    limit: Optional[int] = None,
) -> pd.DataFrame:
    """
    Fetch telemetry for a single device in a time window.

    Returns a pandas DataFrame sorted by timestamp.
    """
    stmt = (
        select(TelemetryRecord)
        .where(
            TelemetryRecord.device_id == device_id,
            TelemetryRecord.timestamp >= start,
            TelemetryRecord.timestamp < end,
        )
        .order_by(TelemetryRecord.timestamp.asc())
    )

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

def fetch_latest_per_device(n: int = 10) -> pd.DataFrame:
    """
    Fetch latest N rows across all devices (useful for dashboard-like checks).
    """
    stmt = (
        select(TelemetryRecord)
        .order_by(TelemetryRecord.timestamp.desc())
        .limit(int(n))
    )

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