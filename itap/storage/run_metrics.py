from __future__ import annotations

import json

from itap.storage.metrics import (
    row_count,
    time_bounds,
    rows_per_device,
    anomaly_rate,
    error_code_rate,
)

def main() -> None:
    total = row_count()
    mn, mx = time_bounds()

    print(f"Rows: {total:,}")
    print(f"Time bounds: {mn} → {mx}\n")

    print("Top devices by rows:")
    print(rows_per_device(10))

    print("\nAnomaly stats:")
    print(json.dumps(anomaly_rate(), indent=2))

    print("\nError code stats:")
    print(json.dumps(error_code_rate(), indent=2))

if __name__ == "__main__":
    main()