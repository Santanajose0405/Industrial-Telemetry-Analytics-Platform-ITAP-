"""
Shared test fixtures for alert rules testing.

Provides reusable test data, mock configurations, and utility functions
to keep individual test files clean and focused.

Design intent:
- Keep conftest.py "stable" and independent of implementation details.
- Provide DataFrames that resemble run_score outputs:
  timestamp, device_id, state, score, pred, anomaly_tag, families_sorted, top_features
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

import pandas as pd
import pytest


# ============================================================================
# Time-based fixtures
# ============================================================================

@pytest.fixture
def base_timestamp() -> datetime:
    """Base timestamp for all time-based tests."""
    return datetime(2026, 1, 1, 10, 0, 0)


@pytest.fixture
def timestamps_within_window(base_timestamp: datetime) -> List[datetime]:
    """Generate timestamps within a 15-minute burst window."""
    return [
        base_timestamp,
        base_timestamp + timedelta(minutes=5),
        base_timestamp + timedelta(minutes=10),
    ]


@pytest.fixture
def timestamps_outside_window(base_timestamp: datetime) -> List[datetime]:
    """Generate timestamps outside a 15-minute burst window."""
    return [
        base_timestamp,
        base_timestamp + timedelta(minutes=20),
        base_timestamp + timedelta(minutes=40),
    ]


@pytest.fixture
def timestamps_exact_boundary(base_timestamp: datetime) -> List[datetime]:
    """Generate timestamps exactly at 15-minute boundaries."""
    return [
        base_timestamp,
        base_timestamp + timedelta(minutes=15),  # Exactly at boundary
        base_timestamp + timedelta(minutes=30),
    ]


# ============================================================================
# Sensor family fixtures
# ============================================================================

@pytest.fixture
def voltage_dominant_families():
    """Sensor families with Voltage dominance (>45%)."""
    return [
        ("Voltage", 48.0),
        ("Temperature", 20.0),
        ("Current", 15.0),
        ("RPM", 10.0),
        ("Vibration", 7.0),
    ]


@pytest.fixture
def temperature_dominant_families():
    """Sensor families with Temperature dominance (>28%)."""
    return [
        ("Temperature", 35.0),
        ("Voltage", 25.0),
        ("Current", 20.0),
        ("RPM", 12.0),
        ("Vibration", 8.0),
    ]


@pytest.fixture
def vibration_rpm_dominant_families():
    """Sensor families with Vibration + RPM dominance (mechanical wear)."""
    return [
        ("Vibration", 30.0),
        ("RPM", 25.0),
        ("Temperature", 20.0),
        ("Current", 15.0),
        ("Voltage", 10.0),
    ]


@pytest.fixture
def balanced_families():
    """Sensor families with no clear dominance."""
    return [
        ("Voltage", 22.0),
        ("Temperature", 21.0),
        ("Current", 20.0),
        ("RPM", 19.0),
        ("Vibration", 18.0),
    ]


@pytest.fixture
def missing_family_data():
    """Empty or incomplete family data."""
    return []


# ============================================================================
# Feature contribution fixtures
# ============================================================================

@pytest.fixture
def sample_top_features():
    """Sample top contributing features."""
    return [
        ("voltage_v_trend", 6.0),
        ("voltage_v_mean", 5.9),
        ("voltage_v_min", 5.9),
        ("voltage_v_max", 5.4),
        ("temp_c_max", 5.2),
    ]


# ============================================================================
# Event dataframe fixtures
# ============================================================================

@pytest.fixture
def single_device_events(base_timestamp, voltage_dominant_families, sample_top_features):
    """Create events for a single device within burst window."""
    data = []
    for i, ts in enumerate([base_timestamp + timedelta(minutes=i * 5) for i in range(3)]):
        data.append(
            {
                "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "device_id": "DEV-001",
                "state": "RUN",
                "score": 0.15 + i * 0.01,
                "pred": 1,
                "anomaly_tag": "power_spike",
                "families_sorted": voltage_dominant_families,
                "top_features": sample_top_features,
            }
        )
    return pd.DataFrame(data)


@pytest.fixture
def multi_device_events(base_timestamp, voltage_dominant_families, sample_top_features):
    """Create events for multiple devices (should NOT trigger burst)."""
    data = []
    devices = ["DEV-001", "DEV-002", "DEV-003"]
    for i, device in enumerate(devices):
        data.append(
            {
                "timestamp": (base_timestamp + timedelta(minutes=i * 5)).strftime("%Y-%m-%d %H:%M:%S"),
                "device_id": device,
                "state": "RUN",
                "score": 0.15,
                "pred": 1,
                "anomaly_tag": "power_spike",
                "families_sorted": voltage_dominant_families,
                "top_features": sample_top_features,
            }
        )
    return pd.DataFrame(data)


@pytest.fixture
def sparse_events(base_timestamp, voltage_dominant_families, sample_top_features):
    """Create events too far apart to trigger burst."""
    data = []
    for i in range(3):
        data.append(
            {
                "timestamp": (base_timestamp + timedelta(minutes=i * 20)).strftime("%Y-%m-%d %H:%M:%S"),
                "device_id": "DEV-001",
                "state": "RUN",
                "score": 0.15,
                "pred": 1,
                "anomaly_tag": "power_spike",
                "families_sorted": voltage_dominant_families,
                "top_features": sample_top_features,
            }
        )
    return pd.DataFrame(data)


@pytest.fixture
def tagged_events(base_timestamp, vibration_rpm_dominant_families, sample_top_features):
    """Create events with various anomaly tags for routing tests."""
    tags = ["bearing_wear", "overheat_drift", "power_spike", None]
    data = []
    for i, tag in enumerate(tags):
        data.append(
            {
                "timestamp": (base_timestamp + timedelta(minutes=i)).strftime("%Y-%m-%d %H:%M:%S"),
                "device_id": f"DEV-00{i+1}",
                "state": "RUN",
                "score": 0.15,
                "pred": 1,
                "anomaly_tag": tag,
                "families_sorted": vibration_rpm_dominant_families,
                "top_features": sample_top_features,
            }
        )
    return pd.DataFrame(data)


# ============================================================================
# Rule configuration fixtures (YAML schema-aligned)
# ============================================================================

@pytest.fixture
def burst_rule_config():
    """Burst alert rule configuration."""
    return {
        "name": "test_burst",
        "type": "burst",
        "device_window_minutes": 15,
        "min_anomalies": 3,
        "severity": "critical",
        "cause": "Repeated anomalies detected",
    }


@pytest.fixture
def dominant_family_rule_config():
    """Dominant family rule configuration."""
    return {
        "name": "test_voltage_dominant",
        "type": "dominant_family",
        "family": "Voltage",
        "min_percent": 45.0,
        "severity": "critical",
        "cause": "Power instability",
    }


@pytest.fixture
def tag_route_rule_config():
    """Tag routing rule configuration."""
    return {
        "name": "test_bearing_route",
        "type": "tag_route",
        "tag": "bearing_wear",
        "route": "maintenance",
        "severity": "warning",
        "cause": "Mechanical degradation",
    }

@pytest.fixture
def critical_score_row(voltage_dominant_families, sample_top_features):
    """Row with critical severity score (above the critical threshold used in tests)."""
    return pd.Series(
        {
            "timestamp": "2026-01-01 10:00:00",
            "device_id": "DEV-001",
            "state": "RUN",
            "score": 0.18,  # should exceed critical threshold used in your tests
            "pred": 1,
            "anomaly_tag": "power_spike",
            "families_sorted": voltage_dominant_families,
            "top_features": sample_top_features,
        }
    )


@pytest.fixture
def info_score_row(balanced_families, sample_top_features):
    """Row with info severity score (below warning threshold used in tests)."""
    return pd.Series(
        {
            "timestamp": "2026-01-01 10:00:00",
            "device_id": "DEV-001",
            "state": "RUN",
            "score": 0.08,  # should be below warning threshold used in your tests
            "pred": 1,
            "anomaly_tag": "",
            "families_sorted": balanced_families,
            "top_features": sample_top_features,
        }
    )

# ============================================================================
# Utility functions for tests
# ============================================================================

def create_event_dataframe(
    device_id: str,
    timestamps: List[datetime],
    scores: List[float],
    families: List[tuple],
    tags: List[str] | None = None,
) -> pd.DataFrame:
    """Helper to create custom event dataframes for tests."""
    if tags is None:
        tags = [""] * len(timestamps)

    data = []
    for ts, score, tag in zip(timestamps, scores, tags):
        data.append(
            {
                "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "device_id": device_id,
                "state": "RUN",
                "score": score,
                "pred": 1,
                "anomaly_tag": tag,
                "families_sorted": families,
                "top_features": [("feature_1", 10.0), ("feature_2", 9.0)],
            }
        )
    return pd.DataFrame(data)
