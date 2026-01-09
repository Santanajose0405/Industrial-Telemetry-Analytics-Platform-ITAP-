"""
SQLAlchemy models for telemetry storage.

This schema is optimized for:
- Time-series queries
- Device-based filtering
- ML feature extraction
"""

from sqlalchemy import Column, Integer, Float, String, DateTime, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class TelemetryRecord(Base):
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True)

    timestamp = Column(DateTime, index=True, nullable=False)
    device_id = Column(String, index=True, nullable=False)
    state = Column(String, nullable=False)

    rpm = Column(Integer)
    temp_c = Column(Float)
    vibration_g = Column(Float)
    current_a = Column(Float)
    voltage_v = Column(Float)

    error_code = Column(Integer)
    anomaly_tag = Column(String)

    __table_args__ = (
        Index("ix_device_timestamp", "device_id", "timestamp"),
    )
