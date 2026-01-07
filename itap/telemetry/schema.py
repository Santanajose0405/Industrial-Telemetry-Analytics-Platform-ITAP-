"""
Telemetry schema definitions.

This module defines the canonical telemetry column layout used across the entire pipeline (generation, ingestion, validation, storage, and modeling).

Keeping the schema centralized ensures:
- Consistent column names
- Easier validation and documentation
- Fewer downstream integration bugs
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

# Ordered list of columns expected in telemetry datasets.
# This order is intentionally row-oriented to support CSV and SQL backends
TELEMETRY_COLUMNS: List[str] = [
    "timestamp",           # ISO 8601 string, Event timestamp"
    "device_id",            # String, Unique identifier for a physical device"
    "state",                    # Operating state (RUN, IDLE, MAINT)"
    "rpm",                     # Integer, Rotations per minute"
    "temp_c",                # Float, Temperature in Celsius"
    "vibration_g",         # Float, Vibration level in g-force"
    "current_a",            # Float, Electrical current in Amperes"
    "voltage_v",            # Float, Electrical voltage in Volts"
    "error_code",          # String, 0 = OK, non-zero indicates device-reported fault"
    "anomaly_tag",       # Simulator-injected fault label (used for ML evaluation"
    ]

@dataclass(frozen=True)
class TelemetrySchema:
    """
    Lightweight schema container.
    
    This class exists primarily for documentation and validation.
    It avoids hard-coding column names throughout the codebase.
    """
    columns: List[str] = None

    def __post_init__(self) -> None:
        # Ensure the schema always reflects the canonical column order
        object.__setattr__(self, "columns", TELEMETRY_COLUMNS)

    def as_dict(self) -> Dict[str, str]:
        """
        Return a human-readable description of each column.
        
        Useful for:
        - Auto-generated documentation
        - Validation error messages
        - Onboarding new contributors
        """
        return {
            "timestamp": "ISO 8601 timestamp for the measurement.",
            "device_id": "Unique device identifier. (e.g., DEV-0001).",
            "state": "Operating state: RUN | IDLE | MAINT.",
            "rpm": "Rotations speed (integer).",
            "temp_c": "Temperature in degrees Celsius.",
            "vibration_g": "Measured vibration in g-force.",
            "current_a": "Electrical current draw in amps.", 
            "voltage_v": "Supply voltage in volts.", 
            "error_code": "0 if OK; non-zero indicates a device-reported error.",
            "anomaly_tag": "Simulator-injected fault label (ground truth)."
        }
       

