from __future__ import annotations

from pathlib import Path
import pandas as pd
import pytest
from sqlalchemy.orm import sessionmaker

from itap.storage.database import make_engine
from itap.storage.ingest import ingest_csv
from itap.telemetry.generator import TelemetryConfig, generate_telemetry

def _make_csv(tmp_path: Path, rows: int = 2000) -> str:
    cfg = TelemetryConfig(
        n_devices=3,
        seed=7, 
        start_time=pd.Timestamp("2026-01-01").to_pydatetime(),
        hours=1,
        freq_seconds=1,
        faults_enabled=True,
        fault_rate=0.05,
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

def test_ingest_is_idempotent(tmp_path: Path):
    # Create isolated DB for this test
    db_path = tmp_path / "test.db"
    engine = make_engine(f"sqlite:///{db_path}")
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)  

    csv_path = _make_csv(tmp_path)

    first = ingest_csv(csv_path, engine=engine, session_factory=session_factory)
    second = ingest_csv(csv_path, engine=engine, session_factory=session_factory)

    assert first > 0    
    assert second == 0  # No new rows on second ingest