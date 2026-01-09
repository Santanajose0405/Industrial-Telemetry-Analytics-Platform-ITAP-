import pandas as pd

from itap.telemetry.generator import TelemetryConfig, generate_telemetry
from itap.validation.validators import (
    validate_schema,
    missing_value_rates,
    range_checks,
)

def _make_small_df(rows: int = 2000) -> pd.DataFrame:
    """Generate a small telemetry DataFrame for testing."""
    cfg = TelemetryConfig(
        n_devices=5,
        seed=123,
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
        return pd.DataFrame(data)

def test_schema_valid_for_generated_data():
    df = _make_small_df()
    result = validate_schema(df)
    assert result["schema_valid"] is True
    assert result["missing_columns"] == []

def test_missing_rates_are_reasonable():
    df = _make_small_df()
    rates = missing_value_rates(df)

    # Missing data may occur due to sensor_dropout faults; ensure it is present but not extreme
    assert 0.0 <= rates["temp_c"] <= 0.20
    assert 0.0 <= rates["vibration_g"] <= 0.20
    assert 0.0 <= rates["current_a"] <= 0.20

def test_ranges_have_noissues():
    df = _make_small_df()
    issues = range_checks(df)

    # Generator should never produce these sanity violations
    assert issues["rpm_negative"] == 0
    assert issues["temp_out_of_bounds"] == 0
    assert issues["voltage_out_of_bounds"] == 0