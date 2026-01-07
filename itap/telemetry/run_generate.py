"""
CLI entry point for telemetry generation.

This script ties together:
- YAML-based configuration
- Telemetry generation
- Output serialization 

It exist so the generator can be run without importing
Python modules manually.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import yaml

from itap.telemetry.generator import TelemetryConfig, generate_telemetry

def load_config(path: str) -> Dict[str, Any]:
    """Load YAML configuration from the specified file path."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main() -> None:
    cfg = load_config("configs/local.example.yaml")

    tcfg = cfg["telemetry"]
    signals = cfg["signals"]
    faults = cfg["faults"]
    out = cfg["output"]

    telemetry_cfg = TelemetryConfig(
        n_devices=int(tcfg["n_devices"]),
        seed=int(tcfg["seed"]),
        start_time=datetime.fromisoformat(tcfg["start_time"]), 
        hours=int(tcfg["hours"]),
        freq_seconds=int(tcfg["freq_seconds"]),
        rpm_base=int(signals["rpm_base"]),
        temp_base_c=float(signals["temp_base_c"]),
        vib_base=float(signals["vib_base"]),
        current_base_a=float(signals["current_base_a"]),
        faults_enabled=bool(faults["enabled"]),
        fault_rate=float(faults["fault_rate"]),
        fault_types=tuple(faults["types"]),
    )

    rows = list(generate_telemetry(telemetry_cfg))
    df = pd.DataFrame(rows)

    out_dir = Path(out["dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "telemetry_sample.csv"

    df.to_csv(out_file, index=False)
    print(f"Wrote {len(df):,} rows to {out_file}")


if __name__ == "__main__":
    main()