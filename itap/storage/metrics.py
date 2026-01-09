"""
Operational metrics for telemetry datasets stored in SQL.

These metrics support:
- dashboard monitoring
- troubleshooting and incident response
- baseline statistics for ML feature engineering
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional, Tuple

import pandas as pd
from sqlalchemy import func, select

from itap.storage.database import SessionLocal
from itap.storage.models import TelemetryRecord

def row_count() -> int:
    """ Total rows in telemetry table."""
    with SessionLocal() as session:
        return int(session.execute(select(func.count()).select_from(TelemetryRecord)).scalar_one())

def time_bounds() -> Tuple[Optional[datetime], Optional[datetime]]:
    """ min/max timestamp in telemetry table."""
    with SessionLocal() as session:
        mn = session.execute(select(func.min(TelemetryRecord.timestamp))).scalar_one()
        mx = session.execute(select(func.max(TelemetryRecord.timestamp))).scalar_one()
    return mn, mx

def rows_per_device(top_n: int = 10) -> pd.DataFrame:
    """Top devices by row count."""
    stmt = (
        select(TelemetryRecord.device_id, func.count().label("rows"))
        .group_by(TelemetryRecord.device_id)
        .order_by(func.count().desc())
        .limit(int(top_n))
    )
    with SessionLocal() as session:
        rows = session.execute(stmt).all()

    return pd.DataFrame(rows, columns=["device_id", "rows"])


def anomaly_rate() -> Dict[str, float]:
    """
    Fraction of rows with a non-empty anomaly tag, and breakdown by tag.
    """
    with SessionLocal() as session:
        total = session.execute(select(func.count()).select_from(TelemetryRecord)).scalar_one()
        tagged = session.execute(
            select(func.count()).where(TelemetryRecord.anomaly_tag != "")
        ).scalar_one()

        by_tag = session.execute(
            select(TelemetryRecord.anomaly_tag, func.count().label("rows"))
            .where(TelemetryRecord.anomaly_tag != "")
            .group_by(TelemetryRecord.anomaly_tag)
            .order_by(func.count().desc())
        ).all()

    total = float(total) if total else 0.0
    tagged = float(tagged) if tagged else 0.0

    return {
        "anomaly_rate": (tagged / total) if total else 0.0,
        "by_tag": {tag: int(cnt) for tag, cnt in by_tag},
    }


def error_code_rate() -> Dict[str, float]:
    """Fraction of rows with non-zero error codes, and breakdown by code."""
    with SessionLocal() as session:
        total = session.execute(select(func.count()).select_from(TelemetryRecord)).scalar_one()
        errored = session.execute(
            select(func.count()).where(TelemetryRecord.error_code != 0)
        ).scalar_one()

        by_code = session.execute(
            select(TelemetryRecord.error_code, func.count().label("rows"))
            .where(TelemetryRecord.error_code != 0)
            .group_by(TelemetryRecord.error_code)
            .order_by(func.count().desc())
        ).all()

    total = float(total) if total else 0.0
    errored = float(errored) if errored else 0.0

    return {
        "error_rate": (errored / total) if total else 0.0,
        "by_code": {str(code): int(cnt) for code, cnt in by_code},
    }

