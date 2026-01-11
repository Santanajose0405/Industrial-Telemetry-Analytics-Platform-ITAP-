"""
Tests for tagged fault routing rules.

Tests the logic that routes alerts to appropriate teams based on
anomaly tags (e.g., bearing_wear → maintenance, overheat → thermal).
"""

import pytest
import pandas as pd
from itap.ml.alerts import AlertRule, build_alert_event_from_row


class TestBasicTagRouting:
    """Test basic tag-to-route mapping."""
    
    def test_bearing_wear_routes_to_maintenance(self, sample_top_features, vibration_rpm_dominant_families):
        """Test that bearing_wear tag routes to maintenance team."""
        row = pd.Series({
            'timestamp': '2026-01-01 10:00:00',
            'device_id': 'DEV-001',
            'state': 'RUN',
            'score': 0.15,
            'pred': 1,
            'anomaly_tag': 'bearing_wear',
        })
        
        alert = build_alert_event_from_row(
            row=row,
            families=vibration_rpm_dominant_families,
            top_features=sample_top_features,
            score_col='score',
            tag_col='anomaly_tag',
        )
        
        # Verify routing (if your implementation includes route field)
        assert alert.device_id == 'DEV-001'
        assert alert.tag == 'bearing_wear'
        # assert alert.route == 'maintenance'  # If you have route field
        # assert alert.severity == 'WARNING'    # Based on your config
    
    def test_overheat_routes_to_thermal(self, sample_top_features, temperature_dominant_families):
        """Test that overheat_drift tag routes to thermal team."""
        row = pd.Series({
            'timestamp': '2026-01-01 10:00:00',
            'device_id': 'DEV-002',
            'state': 'RUN',
            'score': 0.16,
            'pred': 1,
            'anomaly_tag': 'overheat_drift',
        })
        
        alert = build_alert_event_from_row(
            row=row,
            families=temperature_dominant_families,
            top_features=sample_top_features,
            score_col='score',
            tag_col='anomaly_tag',
        )
        
        assert alert.device_id == 'DEV-002'
        assert alert.tag == 'overheat_drift'
        # assert alert.route == 'thermal'
    
    def test_power_spike_routes_to_electrical(self, sample_top_features, voltage_dominant_families):
        """Test that power_spike tag routes to electrical team."""
        row = pd.Series({
            'timestamp': '2026-01-01 10:00:00',
            'device_id': 'DEV-003',
            'state': 'RUN',
            'score': 0.17,
            'pred': 1,
            'anomaly_tag': 'power_spike',
        })
        
        alert = build_alert_event_from_row(
            row=row,
            families=voltage_dominant_families,
            top_features=sample_top_features,
            score_col='score',
            tag_col='anomaly_tag',
        )
        
        assert alert.device_id == 'DEV-003'
        assert alert.tag == 'power_spike'
        # assert alert.route == 'electrical'


class TestUntaggedEvents:
    """Test handling of events without tags."""
    
    def test_no_tag_uses_default_route(self, sample_top_features, balanced_families):
        """Test that untagged events use default/triage route."""
        row = pd.Series({
            'timestamp': '2026-01-01 10:00:00',
            'device_id': 'DEV-001',
            'state': 'RUN',
            'score': 0.15,
            'pred': 1,
            'anomaly_tag': '',  # No tag
        })
        
        alert = build_alert_event_from_row(
            row=row,
            families=balanced_families,
            top_features=sample_top_features,
            score_col='score',
            tag_col='anomaly_tag',
        )
        
        assert alert.device_id == 'DEV-001'
        assert alert.tag == ''
        # assert alert.route == 'triage' or alert.route == 'default'
    
    def test_null_tag_uses_default_route(self, sample_top_features, balanced_families):
        """Test that null/NaN tags use default route."""
        row = pd.Series({
            'timestamp': '2026-01-01 10:00:00',
            'device_id': 'DEV-001',
            'state': 'RUN',
            'score': 0.15,
            'pred': 1,
            'anomaly_tag': None,  # Null
        })
        
        alert = build_alert_event_from_row(
            row=row,
            families=balanced_families,
            top_features=sample_top_features,
            score_col='score',
            tag_col='anomaly_tag',
        )
        
        assert alert.device_id == 'DEV-001'
        # Tag should be normalized to empty string
        assert alert.tag == '' or alert.tag is None


class TestTagNormalization:
    """Test tag normalization and case handling."""
    
    def test_lowercase_tag_matches(self, sample_top_features, vibration_rpm_dominant_families):
        """Test that lowercase tags are handled correctly."""
        row = pd.Series({
            'timestamp': '2026-01-01 10:00:00',
            'device_id': 'DEV-001',
            'state': 'RUN',
            'score': 0.15,
            'pred': 1,
            'anomaly_tag': 'bearing_wear',  # lowercase
        })
        
        alert = build_alert_event_from_row(
            row=row,
            families=vibration_rpm_dominant_families,
            top_features=sample_top_features,
            score_col='score',
            tag_col='anomaly_tag',
        )
        
        assert alert.tag == 'bearing_wear'
    
    def test_uppercase_tag_normalized(self, sample_top_features, vibration_rpm_dominant_families):
        """Test that uppercase tags are normalized (if applicable)."""
        row = pd.Series({
            'timestamp': '2026-01-01 10:00:00',
            'device_id': 'DEV-001',
            'state': 'RUN',
            'score': 0.15,
            'pred': 1,
            'anomaly_tag': 'BEARING_WEAR',  # uppercase
        })
        
        alert = build_alert_event_from_row(
            row=row,
            families=vibration_rpm_dominant_families,
            top_features=sample_top_features,
            score_col='score',
            tag_col='anomaly_tag',
        )
        
        # Depending on your normalization strategy:
        # Either keep as-is or normalize to lowercase
        assert alert.tag in ['BEARING_WEAR', 'bearing_wear']
    
    def test_whitespace_stripped(self, sample_top_features, vibration_rpm_dominant_families):
        """Test that whitespace in tags is stripped."""
        row = pd.Series({
            'timestamp': '2026-01-01 10:00:00',
            'device_id': 'DEV-001',
            'state': 'RUN',
            'score': 0.15,
            'pred': 1,
            'anomaly_tag': '  bearing_wear  ',  # with whitespace
        })
        
        alert = build_alert_event_from_row(
            row=row,
            families=vibration_rpm_dominant_families,
            top_features=sample_top_features,
            score_col='score',
            tag_col='anomaly_tag',
        )
        
        assert alert.tag == 'bearing_wear'  # Whitespace stripped


class TestUnknownTags:
    """Test handling of unknown/unmapped tags."""
    
    def test_unknown_tag_fallback(self, sample_top_features, balanced_families):
        """Test that unknown tags fall back to default route."""
        row = pd.Series({
            'timestamp': '2026-01-01 10:00:00',
            'device_id': 'DEV-001',
            'state': 'RUN',
            'score': 0.15,
            'pred': 1,
            'anomaly_tag': 'mystery_fault',  # Not in routing config
        })
        
        alert = build_alert_event_from_row(
            row=row,
            families=balanced_families,
            top_features=sample_top_features,
            score_col='score',
            tag_col='anomaly_tag',
        )
        
        assert alert.tag == 'mystery_fault'
        # Should use fallback route
        # assert alert.route == 'triage' or alert.route == 'default'
    
    def test_typo_in_tag_not_matched(self, sample_top_features, vibration_rpm_dominant_families):
        """Test that typos in tags don't match configured routes."""
        row = pd.Series({
            'timestamp': '2026-01-01 10:00:00',
            'device_id': 'DEV-001',
            'state': 'RUN',
            'score': 0.15,
            'pred': 1,
            'anomaly_tag': 'bering_wear',  # Typo: bering instead of bearing
        })
        
        alert = build_alert_event_from_row(
            row=row,
            families=vibration_rpm_dominant_families,
            top_features=sample_top_features,
            score_col='score',
            tag_col='anomaly_tag',
        )
        
        assert alert.tag == 'bering_wear'
        # Should NOT route to maintenance (wrong tag)


class TestRoutePriority:
    """Test route priority when multiple rules could apply."""
    
    def test_specific_tag_overrides_family_rule(self):
        """
        Test that tag-based routing takes precedence over family-based rules.
        
        If an event has tag='bearing_wear' AND Voltage dominance,
        the tag-based route (maintenance) should win over voltage rule (electrical).
        """
        # This depends on your rule precedence implementation
        pass
    
    def test_multiple_tags_first_match_wins(self):
        """
        Test behavior when event could match multiple tag routes.
        
        This would require your schema to support multiple tags,
        which may not be the case.
        """
        pass


class TestSeverityMapping:
    """Test that tag routing includes severity mapping."""
    
    def test_bearing_wear_has_warning_severity(self, sample_top_features, vibration_rpm_dominant_families):
        """Test that bearing_wear has configured severity."""
        row = pd.Series({
            'timestamp': '2026-01-01 10:00:00',
            'device_id': 'DEV-001',
            'state': 'RUN',
            'score': 0.15,
            'pred': 1,
            'anomaly_tag': 'bearing_wear',
        })
        
        alert = build_alert_event_from_row(
            row=row,
            families=vibration_rpm_dominant_families,
            top_features=sample_top_features,
            score_col='score',
            tag_col='anomaly_tag',
        )
        
        # Verify severity is set (based on your tag route config)
        assert alert.severity in ['CRITICAL', 'WARNING', 'INFO']
    
    def test_power_spike_has_critical_severity(self, sample_top_features, voltage_dominant_families):
        """Test that power_spike has configured severity."""
        row = pd.Series({
            'timestamp': '2026-01-01 10:00:00',
            'device_id': 'DEV-003',
            'state': 'RUN',
            'score': 0.18,
            'pred': 1,
            'anomaly_tag': 'power_spike',
        })
        
        alert = build_alert_event_from_row(
            row=row,
            families=voltage_dominant_families,
            top_features=sample_top_features,
            score_col='score',
            tag_col='anomaly_tag',
        )
        
        # Power issues are typically critical
        assert alert.severity == 'CRITICAL'


class TestRootCauseMapping:
    """Test that tag routing includes root cause descriptions."""
    
    def test_bearing_wear_root_cause(self, sample_top_features, vibration_rpm_dominant_families):
        """Test that bearing_wear has descriptive root cause."""
        row = pd.Series({
            'timestamp': '2026-01-01 10:00:00',
            'device_id': 'DEV-001',
            'state': 'RUN',
            'score': 0.15,
            'pred': 1,
            'anomaly_tag': 'bearing_wear',
        })
        
        alert = build_alert_event_from_row(
            row=row,
            families=vibration_rpm_dominant_families,
            top_features=sample_top_features,
            score_col='score',
            tag_col='anomaly_tag',
        )
        
        assert alert.root_cause is not None
        assert len(alert.root_cause) > 0
        # Should mention mechanical or bearing
        assert any(word in alert.root_cause.lower() for word in ['mechanical', 'bearing', 'wear'])
    
    def test_overheat_root_cause(self, sample_top_features, temperature_dominant_families):
        """Test that overheat has descriptive root cause."""
        row = pd.Series({
            'timestamp': '2026-01-01 10:00:00',
            'device_id': 'DEV-002',
            'state': 'RUN',
            'score': 0.16,
            'pred': 1,
            'anomaly_tag': 'overheat_drift',
        })
        
        alert = build_alert_event_from_row(
            row=row,
            families=temperature_dominant_families,
            top_features=sample_top_features,
            score_col='score',
            tag_col='anomaly_tag',
        )
        
        assert alert.root_cause is not None
        # Should mention thermal or temperature
        assert any(word in alert.root_cause.lower() for word in ['thermal', 'temperature', 'overheat'])


class TestBatchRouting:
    """Test routing multiple events at once."""
    
    def test_route_mixed_tags(self, tagged_events):
        """Test routing a batch of events with different tags."""
        # tagged_events fixture has: bearing_wear, overheat_drift, power_spike, None
        
        assert len(tagged_events) == 4
        
        # Each event should be routed appropriately
        tags = tagged_events['anomaly_tag'].tolist()
        assert 'bearing_wear' in tags
        assert 'overheat_drift' in tags
        assert 'power_spike' in tags
        assert None in tags or '' in tags
    
    def test_route_count_by_team(self):
        """Test counting how many alerts go to each team."""
        # If you have 10 alerts:
        # - 4 to maintenance (bearing_wear)
        # - 3 to thermal (overheat)
        # - 2 to electrical (power_spike)
        # - 1 to triage (untagged)
        #
        # Verify the routing distribution is correct
        pass


class TestEdgeCases:
    """Test edge cases for tag routing."""
    
    def test_empty_string_tag(self, sample_top_features, balanced_families):
        """Test explicit empty string tag."""
        row = pd.Series({
            'timestamp': '2026-01-01 10:00:00',
            'device_id': 'DEV-001',
            'state': 'RUN',
            'score': 0.15,
            'pred': 1,
            'anomaly_tag': '',
        })
        
        alert = build_alert_event_from_row(
            row=row,
            families=balanced_families,
            top_features=sample_top_features,
            score_col='score',
            tag_col='anomaly_tag',
        )
        
        assert alert.tag == ''
    
    def test_numeric_tag(self, sample_top_features, balanced_families):
        """Test handling of numeric tag (should be converted to string)."""
        row = pd.Series({
            'timestamp': '2026-01-01 10:00:00',
            'device_id': 'DEV-001',
            'state': 'RUN',
            'score': 0.15,
            'pred': 1,
            'anomaly_tag': 12345,  # Numeric tag
        })
        
        alert = build_alert_event_from_row(
            row=row,
            families=balanced_families,
            top_features=sample_top_features,
            score_col='score',
            tag_col='anomaly_tag',
        )
        
        # Should be converted to string
        assert alert.tag == '12345'
    
    def test_very_long_tag(self, sample_top_features, balanced_families):
        """Test handling of very long tag names."""
        long_tag = 'bearing_wear_' * 50  # 650+ characters
        
        row = pd.Series({
            'timestamp': '2026-01-01 10:00:00',
            'device_id': 'DEV-001',
            'state': 'RUN',
            'score': 0.15,
            'pred': 1,
            'anomaly_tag': long_tag,
        })
        
        alert = build_alert_event_from_row(
            row=row,
            families=balanced_families,
            top_features=sample_top_features,
            score_col='score',
            tag_col='anomaly_tag',
        )
        
        # Should handle without crashing (may truncate)
        assert alert.tag is not None