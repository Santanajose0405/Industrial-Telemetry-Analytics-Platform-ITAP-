from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy.orm import sessionmaker

from itap.telemetry.generator import TelemetryConfig, generate_telemetry
from itap.storage.database import make_engine
from itap.storage.ingest import ingest_csv
from itap.storage.models import Base
from itap.storage import metrics as m


def _make_csv(tmp_path: Path, rows: int = 1000) -> str:
    cfg = TelemetryConfig(
        n_devices=2,
        seed=9,
        start_time=pd.Timestamp("2026-01-01").to_pydatetime(),
        hours=1,
        freq_seconds=1,
        faults_enabled=True,
        fault_rate=0.10,
    )
    data = []
    for i, row in enumerate(generate_telemetry(cfg)):
        data.append(row)
        if i >= rows - 1:
            break
    df = pd.DataFrame(data)
    csv_path = tmp_path / "sample.csv"
    df.to_csv(csv_path, index=False)
    return str(csv_path)


def test_metrics_smoke(tmp_path: Path, monkeypatch):
    # Isolated DB
    db_path = tmp_path / "test.db"
    engine = make_engine(f"sqlite:///{db_path}")
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    # Create tables in isolated DB
    Base.metadata.create_all(bind=engine)

    csv_path = _make_csv(tmp_path)
    ingest_csv(csv_path, engine=engine, session_factory=session_factory)

    # Monkeypatch SessionLocal in metrics module to use isolated DB
    from itap.storage import database as db
    db.ENGINE = engine
    db.SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    # Re-import metrics to pick up patched SessionLocal
    from importlib import reload
    reload(m)

    assert m.row_count() > 0
    ar = m.anomaly_rate()
    er = m.error_code_rate()
    assert 0.0 <= ar["anomaly_rate"] <= 1.0
    assert 0.0 <= er["error_rate"] <= 1.0
