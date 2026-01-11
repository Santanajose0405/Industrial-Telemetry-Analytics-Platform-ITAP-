"""
Tests for burst-based alert rules.

Tests the logic that triggers alerts when N anomalies occur within
M minutes for the same device (e.g., 3 events within 15 minutes).

CRITICAL: These tests lock in your time window boundary behavior.
Decision: Events at exactly M minutes apart should be INCLUSIVE.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta


# NOTE: Update these imports based on your actual implementation
# You may need to implement evaluate_burst_rule() or similar
# For now, these are placeholder function names


class TestBurstDetectionBasics:
    """Test basic burst detection logic."""
    
    def test_three_events_within_window_triggers(self, single_device_events):
        """
        Test that 3 anomalies within 15 minutes triggers burst alert.
        
        Events at: t+0, t+5, t+10 minutes (all within 15-minute window).
        """
        df = single_device_events
        
        # Your implementation goes here
        # Example: alerts = evaluate_burst_rule(df, window_minutes=15, min_count=3)
        
        # Assertions (adjust based on your implementation):
        assert len(df) == 3
        assert df['device_id'].nunique() == 1  # All same device
        
        # Verify timestamps are within window
        timestamps = pd.to_datetime(df['timestamp'])
        time_range = timestamps.max() - timestamps.min()
        assert time_range <= timedelta(minutes=15)
    
    def test_events_across_devices_no_burst(self, multi_device_events):
        """
        Test that events across different devices don't trigger burst.
        
        3 events at t+0, t+5, t+10, but on DEV-001, DEV-002, DEV-003.
        """
        df = multi_device_events
        
        # Verify test setup
        assert len(df) == 3
        assert df['device_id'].nunique() == 3  # Different devices
        
        # Your burst detection should NOT trigger here
        # Example assertion:
        # alerts = evaluate_burst_rule(df, window_minutes=15, min_count=3)
        # assert len(alerts) == 0
    
    def test_sparse_events_no_burst(self, sparse_events):
        """
        Test that events too far apart don't trigger burst.
        
        3 events at t+0, t+20, t+40 (each > 15 minutes apart).
        """
        df = sparse_events
        
        # Verify test setup
        assert len(df) == 3
        timestamps = pd.to_datetime(df['timestamp'])
        
        # Check that consecutive events are > 15 minutes apart
        for i in range(len(timestamps) - 1):
            gap = timestamps.iloc[i + 1] - timestamps.iloc[i]
            assert gap > timedelta(minutes=15)
        
        # No burst should be detected
        # Example assertion:
        # alerts = evaluate_burst_rule(df, window_minutes=15, min_count=3)
        # assert len(alerts) == 0


class TestTimeWindowBoundaries:
    """
    Test precise time window boundary behavior.
    
    CRITICAL: This locks in your chosen convention (inclusive vs exclusive).
    """
    
    def test_events_exactly_at_boundary_inclusive(self, base_timestamp):
        """
        Test events at exactly 15-minute boundary (INCLUSIVE).
        
        Convention chosen: Events at exactly M minutes ARE included.
        Events at: t+0, t+15 (exactly at boundary), t+30
        
        The window [t+15, t+30] includes event at t+15.
        """
        from conftest import create_event_dataframe
        
        timestamps = [
            base_timestamp,
            base_timestamp + timedelta(minutes=15),  # Exactly at boundary
            base_timestamp + timedelta(minutes=30),
        ]
        
        df = create_event_dataframe(
            device_id='DEV-001',
            timestamps=timestamps,
            scores=[0.15, 0.16, 0.17],
            families=[('Voltage', 50.0)],
        )
        
        # The second and third events should be within a 15-minute window
        # since t+30 - t+15 = 15 minutes exactly
        
        # Your implementation should decide: is this a burst?
        # If INCLUSIVE: Last 2 events (t+15, t+30) form a burst if min_count=2
        # If EXCLUSIVE: They do NOT form a burst
        
        # Lock in your choice here:
        # alerts = evaluate_burst_rule(df, window_minutes=15, min_count=2)
        # assert len(alerts) > 0  # INCLUSIVE
        # OR
        # assert len(alerts) == 0  # EXCLUSIVE
    
    def test_events_one_second_within_boundary(self, base_timestamp):
        """Test events at boundary - 1 second (definitely within)."""
        from conftest import create_event_dataframe
        
        timestamps = [
            base_timestamp,
            base_timestamp + timedelta(minutes=14, seconds=59),  # Just under 15 min
            base_timestamp + timedelta(minutes=29, seconds=58),
        ]
        
        df = create_event_dataframe(
            device_id='DEV-001',
            timestamps=timestamps,
            scores=[0.15] * 3,
            families=[('Voltage', 50.0)],
        )
        
        # These should definitely be within window
        # alerts = evaluate_burst_rule(df, window_minutes=15, min_count=2)
        # assert len(alerts) > 0
    
    def test_events_one_second_outside_boundary(self, base_timestamp):
        """Test events at boundary + 1 second (definitely outside)."""
        from conftest import create_event_dataframe
        
        timestamps = [
            base_timestamp,
            base_timestamp + timedelta(minutes=15, seconds=1),  # Just over 15 min
        ]
        
        df = create_event_dataframe(
            device_id='DEV-001',
            timestamps=timestamps,
            scores=[0.15, 0.16],
            families=[('Voltage', 50.0)],
        )
        
        # These should be outside the window
        # alerts = evaluate_burst_rule(df, window_minutes=15, min_count=2)
        # assert len(alerts) == 0


class TestSlidingWindow:
    """Test sliding window behavior for burst detection."""
    
    def test_overlapping_bursts(self, base_timestamp):
        """
        Test multiple overlapping burst windows.
        
        Events at: t+0, t+5, t+10, t+14, t+18
        
        Windows:
        - [t+0, t+15]: 4 events (t+0, t+5, t+10, t+14)
        - [t+5, t+20]: 3 events (t+5, t+10, t+14, t+18)
        """
        from conftest import create_event_dataframe
        
        timestamps = [
            base_timestamp + timedelta(minutes=m)
            for m in [0, 5, 10, 14, 18]
        ]
        
        df = create_event_dataframe(
            device_id='DEV-001',
            timestamps=timestamps,
            scores=[0.15] * 5,
            families=[('Voltage', 50.0)],
        )
        
        # If min_count=3, multiple windows should trigger
        # Your deduplication logic determines how many alerts are emitted
    
    def test_rolling_window_expiration(self, base_timestamp):
        """
        Test that old events roll out of the window.
        
        Events at: t+0, t+10, t+20, t+25
        
        At t+25:
        - [t+10, t+25]: 3 events (t+10, t+20, t+25) - BURST
        - Event at t+0 has rolled out
        """
        from conftest import create_event_dataframe
        
        timestamps = [
            base_timestamp + timedelta(minutes=m)
            for m in [0, 10, 20, 25]
        ]
        
        df = create_event_dataframe(
            device_id='DEV-001',
            timestamps=timestamps,
            scores=[0.15] * 4,
            families=[('Voltage', 50.0)],
        )
        
        # The last 3 events form a burst, but event at t+0 should not be counted


class TestMinAnomalyThreshold:
    """Test minimum anomaly count thresholds."""
    
    def test_exactly_min_count_triggers(self, base_timestamp):
        """Test that exactly min_count anomalies triggers burst."""
        from conftest import create_event_dataframe
        
        timestamps = [base_timestamp + timedelta(minutes=i*5) for i in range(3)]
        
        df = create_event_dataframe(
            device_id='DEV-001',
            timestamps=timestamps,
            scores=[0.15] * 3,
            families=[('Voltage', 50.0)],
        )
        
        # With min_count=3, this should trigger
        # alerts = evaluate_burst_rule(df, window_minutes=15, min_count=3)
        # assert len(alerts) > 0
    
    def test_below_min_count_no_trigger(self, base_timestamp):
        """Test that fewer than min_count anomalies doesn't trigger."""
        from conftest import create_event_dataframe
        
        timestamps = [base_timestamp, base_timestamp + timedelta(minutes=5)]
        
        df = create_event_dataframe(
            device_id='DEV-001',
            timestamps=timestamps,
            scores=[0.15, 0.16],
            families=[('Voltage', 50.0)],
        )
        
        # With min_count=3, this should NOT trigger
        # alerts = evaluate_burst_rule(df, window_minutes=15, min_count=3)
        # assert len(alerts) == 0
    
    def test_above_min_count_triggers(self, base_timestamp):
        """Test that more than min_count anomalies triggers burst."""
        from conftest import create_event_dataframe
        
        timestamps = [base_timestamp + timedelta(minutes=i*3) for i in range(5)]
        
        df = create_event_dataframe(
            device_id='DEV-001',
            timestamps=timestamps,
            scores=[0.15] * 5,
            families=[('Voltage', 50.0)],
        )
        
        # With min_count=3, this should trigger (5 > 3)
        # alerts = evaluate_burst_rule(df, window_minutes=15, min_count=3)
        # assert len(alerts) > 0


class TestPerDeviceBursts:
    """Test that bursts are tracked per-device."""
    
    def test_two_devices_independent_bursts(self, base_timestamp):
        """Test that each device has independent burst detection."""
        from conftest import create_event_dataframe
        
        # DEV-001: 3 events within window (should trigger)
        df1 = create_event_dataframe(
            device_id='DEV-001',
            timestamps=[base_timestamp + timedelta(minutes=i*5) for i in range(3)],
            scores=[0.15] * 3,
            families=[('Voltage', 50.0)],
        )
        
        # DEV-002: 2 events within window (should NOT trigger if min_count=3)
        df2 = create_event_dataframe(
            device_id='DEV-002',
            timestamps=[base_timestamp + timedelta(minutes=i*5) for i in range(2)],
            scores=[0.15] * 2,
            families=[('Voltage', 50.0)],
        )
        
        df = pd.concat([df1, df2], ignore_index=True)
        
        # Only DEV-001 should trigger burst
        # alerts = evaluate_burst_rule(df, window_minutes=15, min_count=3)
        # assert len(alerts) == 1
        # assert alerts[0].device_id == 'DEV-001'
    
    def test_device_isolation(self, base_timestamp):
        """Test that events from different devices don't contribute to same burst."""
        from conftest import create_event_dataframe
        
        # Mixed device events
        devices = ['DEV-001', 'DEV-001', 'DEV-002', 'DEV-001']
        timestamps = [base_timestamp + timedelta(minutes=i*3) for i in range(4)]
        
        data = []
        for dev, ts in zip(devices, timestamps):
            row = {
                'timestamp': ts.strftime('%Y-%m-%d %H:%M:%S'),
                'device_id': dev,
                'state': 'RUN',
                'score': 0.15,
                'pred': 1,
                'anomaly_tag': '',
                'families_sorted': [('Voltage', 50.0)],
                'top_features': [('feat1', 10.0)],
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # DEV-001 has 3 events: t+0, t+3, t+9 (within 15 min)
        # DEV-002 has 1 event: t+6
        # Only DEV-001 should trigger if min_count=3


class TestBurstAlertContent:
    """Test the content of burst alerts."""
    
    def test_burst_alert_has_correct_severity(self):
        """Test that burst alerts have configured severity."""
        # If your burst rule config specifies severity="critical"
        # The resulting alert should have severity="CRITICAL"
        pass
    
    def test_burst_alert_has_event_count(self):
        """Test that burst alert includes count of anomalies."""
        # Alert should indicate how many events triggered the burst
        # E.g., "5 anomalies within 15 minutes"
        pass
    
    def test_burst_alert_has_time_window(self):
        """Test that burst alert includes the time window."""
        # Alert should indicate the time range of the burst
        # E.g., "2026-01-01 10:00:00 to 2026-01-01 10:14:00"
        pass


class TestDedupBehavior:
    """Test alert deduplication for burst detection."""
    
    def test_no_duplicate_alerts_for_same_burst(self):
        """
        Test that a single burst doesn't generate multiple alerts.
        
        If events at t+0, t+5, t+10 trigger a burst,
        don't emit another burst for t+5, t+10, t+15.
        """
        # This depends on your dedup strategy
        # Options:
        # 1. Cooldown period (no new alerts for X minutes after burst)
        # 2. Group by burst window and emit one alert per window
        # 3. Track "alerted" flag per burst
        pass
    
    def test_separate_bursts_separate_alerts(self):
        """
        Test that distinct bursts generate separate alerts.
        
        Burst 1: t+0, t+5, t+10
        <gap>
        Burst 2: t+60, t+65, t+70
        
        Should generate 2 alerts.
        """
        pass


class TestEdgeCases:
    """Test edge cases for burst detection."""
    
    def test_single_event_no_burst(self, base_timestamp):
        """Test that a single event doesn't trigger burst."""
        from conftest import create_event_dataframe
        
        df = create_event_dataframe(
            device_id='DEV-001',
            timestamps=[base_timestamp],
            scores=[0.15],
            families=[('Voltage', 50.0)],
        )
        
        # Should not trigger burst (need at least min_count events)
    
    def test_zero_window_size(self):
        """Test behavior with zero window size (should be invalid)."""
        # This should either raise an error or be treated as invalid config
        pass
    
    def test_negative_window_size(self):
        """Test behavior with negative window size (should be invalid)."""
        # This should raise an error or validation failure
        pass
    
    def test_very_large_window(self, base_timestamp):
        """Test with very large window (e.g., 1 year)."""
        from conftest import create_event_dataframe
        
        # All events within a year should be considered in same window
        timestamps = [
            base_timestamp,
            base_timestamp + timedelta(days=30),
            base_timestamp + timedelta(days=60),
        ]
        
        df = create_event_dataframe(
            device_id='DEV-001',
            timestamps=timestamps,
            scores=[0.15] * 3,
            families=[('Voltage', 50.0)],
        )
        
        # With window=525600 minutes (1 year), should trigger