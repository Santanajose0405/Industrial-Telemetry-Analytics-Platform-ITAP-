from __future__ import annotations
from datetime import timedelta
import pandas as pd
from itap.storage.query import fetch_latest_per_device, fetch_device_window

def main() -> None:
    # Quick dashboard-style read
    latest = fetch_latest_per_device(10)
    print("\nLatest 10 rows:")
    print(latest)

    # If DB has data, use the first device and a 10-minute windows
    if len(latest) > 0:
        device_id = str(latest.iloc[0]["device_id"])
        end = pd.to_datetime(latest.iloc[0]["timestamp"]).to_pydatetime()
        start = end -timedelta(minutes=10)

        window = fetch_device_window(device_id=device_id, start=start, end=end)
        print(f"\nWindow for {device_id} ({start} → {end}): rows={len(window)}")
        print(window.head())

if __name__ == "__main__":
    main()