"""
Industrial telemetry generator.

This module simulates time-series telemetry data for industrial devices.
It intentionally models:
- Normal operating conditions
- State transitions (RUN, IDLE, MAINT)
- Seasonal patterns
- Fault injection for downstream anomaly detection work

The output is deterministic given a random seed, which is critical for:
- Reproducibility
- Model evaluation
- Debugging
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Iterator, Optional, Tuple

import numpy as np

# Valid machine operating states
STATES = ("RUN", "IDLE", "MAINT")

@dataclass
class TelemetryConfig:
    """
    Configuration for telemetry generation.

    This object decouples configuration from code logic, allowing
    the generator to be driven entirely from external YAML config.
    """
    n_devices: int
    seed: int
    start_time: datetime
    hours: int 
    freq_seconds: int

    rpm_base: int = 1800
    temp_base_c: float = 55.0
    vib_base: float = 0.025
    current_base_a: float = 6.5

    faults_enabled: bool = True
    fault_rate: float = 0.02
    fault_types: Tuple[str, ...] = (
        "overheat_drift", 
        "bearing_wear", 
        "sensor_dropout", 
        "power_spike",
    )

def _device_id(i: int) -> str:
    """Generate a stable, human-readable device ID."""
    return f"DEV-{i:04d}"

def _chose_state(rng: np.random.Generator) -> str:
    """
    Randomly choose an operating state.
    
    RUN is intentionally weighted more heavily to reflect 
    real-world production environments.
    """
    r = rng.random()
    if r < 0.80:
        return "RUN"
    if r < 0.95:
        return "IDLE"
    return "MAINT"

def _seasonal_component(t_idx: int, period: int) -> float:
    """
    Generate a smooth periodic signal.

    This introduces non-stationarity into data,
    forcing ML models to learn more than simple thresholds.
    """
    return float(np.sin(2.0 * np.pi * (t_idx / period)))

def generate_telemetry(cfg: TelemetryConfig) -> Iterator[Dict]:
    """ 
    Generate telemetry recods.

    Yields one dictionary per device per timestep to support
    streaming or batch ingestion models.
    """
    rng = np.random.default_rng(cfg.seed)
    
    total_seconds = cfg.hours * 3600
    steps = max(1, total_seconds // cfg.freq_seconds)
    
    # Device-specific offsets introduce heterogeneity across the fleet)
    rpm_offsets = rng.integers(-120, 120, size=cfg.n_devices)
    temp_offsets = rng.normal(0.0, 2.0, size=cfg.n_devices)
    vib_offsets = rng.normal(0.0, 0.05, size=cfg.n_devices)
    current_offsets = rng.normal(0.0, 0.3, size=cfg.n_devices)

    # Track long-lived faults across timesteps
    active_fault: Dict[str, Optional[str]] = {
        _device_id(i): None for i in range(cfg.n_devices) 
    }
    fault_remaining_steps: Dict[str, int] = {
        _device_id(i): 0 for i in range(cfg.n_devices)
    }

    for t in range(int(steps)):
        ts = cfg.start_time + timedelta(seconds=t * cfg.freq_seconds)
        seasonal =  _seasonal_component(
            t_idx=t,
            period=max(20, int(3600 / cfg.freq_seconds)),
        )

        for i in range(cfg.n_devices):
            did = _device_id(i)
            state = _chose_state(rng)
            
            # Baseline signals with noise and seasonal variation
            rpm = cfg.rpm_base + int(rpm_offsets[i] + 40 * seasonal + rng.normal(0, 15))
            temp_c = cfg.temp_base_c + float(temp_offsets[i] + 1.5 * seasonal + rng.normal(0, 0.4))
            vibration_g = max(
                0.0,
                float(cfg.vib_base + vib_offsets[i] + 0.03 * seasonal + rng.normal(0, 0.01)),
            )
            current_a = max(
                0.0,
                float(cfg.current_base_a + current_offsets[i] + 0.2 * seasonal + rng.normal(0, 0.8)),
            )
            voltage_v = float(24.0 + rng.normal(0, 0.15))
            error_code = 0
            anomaly_tag = " "

            # State-based behavior adjustments
            if state == "IDLE":
                rpm = max(0, int(rpm * 0.10))
                current_a *= 0.55
                vibration_g *= 0.50
            elif state == "MAINT":
                rpm = 0
                current_a *= 0.35
                vibration_g *= 0.35

            # Probabilistically start new faults (only during RUN)
            if cfg.faults_enabled and state == "RUN" and active_fault[did] is None:
                if rng.random() < cfg.fault_rate:
                    ft = str(rng.choice(cfg.fault_types))
                    active_fault[did] = ft
                    fault_remaining_steps[did] = (
                        int(rng.integers(30, 120))
                        if ft in ("overheat_drift", "bearing_wear")
                        else int(rng.integers(1, 6))
                    )

            # Apply active fault effects
            ft = active_fault[did]
            if ft is not None and fault_remaining_steps[did] > 0:
                anomaly_tag = ft

                if ft == "overheat_drift":
                    temp_c += 0.05 * (1 + (120 - fault_remaining_steps[did]) / 10.0)
                    if temp_c > 80:
                        error_code = 2

                elif ft == "bearing_wear":
                    vibration_g += 0.01 * (1 + (120 - fault_remaining_steps[did]) / 12.0)
                    current_a += 0.05
                    if vibration_g > 0.8:
                        error_code = 3

                elif ft == "power_spike":
                    voltage_v += float(rng.normal(2.0, 0.4))
                    current_a += float(rng.normal(1.2, 0.3))
                    error_code = 4

                elif ft == "sensor_dropout":
                    # Missing data is intentionally modeled as NaN
                    if rng.random() < 0.7:
                        temp_c = float("nan")
                        vibration_g = float("nan")
                        current_a = float("nan")
                        error_code = 5

                fault_remaining_steps[did] -= 1
                if fault_remaining_steps[did] <= 0:
                    active_fault[did] = None

            yield {
                "timestamp": ts.isoformat(),
                "device_id": did,
                "state": state,
                "rpm": int(rpm),
                "temp_c": float(temp_c),
                "vibration_g": float(vibration_g),
                "current_a": float(current_a),
                "voltage_v": float(voltage_v),
                "error_code": int(error_code),
                "anomaly_tag": anomaly_tag,
            }