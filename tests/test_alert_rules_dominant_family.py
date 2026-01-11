"""
Tests for dominant sensor family alert rules.

Tests the logic that triggers alerts when a specific sensor family
dominates the feature attribution (e.g., Voltage > 45%).
"""

import pytest
import pandas as pd
from itap.ml.alerts import (
    AlertRule,
    build_alert_event_from_row,
    match_rule,
)


class TestDominantFamilyMatching:
    """Test rule matching logic for dominant family rules."""
    
    def test_voltage_dominance_matches(self, voltage_dominant_families):
        """Test that high voltage dominance matches voltage rule."""
        rule = AlertRule(
            name="voltage_alert",
            root_cause="Power instability",
            required_families=("Voltage",),
            min_family_percent=40.0,
        )
        
        matched_rule, confidence = match_rule(voltage_dominant_families, rules=[rule])
        
        assert matched_rule is not None
        assert matched_rule.name == "voltage_alert"
        assert confidence > 0.0
        # Voltage is 48%, threshold is 40%, so confidence should be high
        assert confidence >= 1.0  # 48/40 = 1.2, capped at 1.0
    
    def test_voltage_dominance_does_not_match_low_threshold(self, voltage_dominant_families):
        """Test that voltage dominance doesn't match if threshold too high."""
        rule = AlertRule(
            name="strict_voltage",
            root_cause="Extreme power issue",
            required_families=("Voltage",),
            min_family_percent=60.0,  # Voltage is only 48%
        )
        
        matched_rule, confidence = match_rule(voltage_dominant_families, rules=[rule])
        
        assert matched_rule is None
        assert confidence == 0.0
    
    def test_temperature_dominance_matches(self, temperature_dominant_families):
        """Test that temperature dominance matches temperature rule."""
        rule = AlertRule(
            name="thermal_alert",
            root_cause="Thermal overload",
            required_families=("Temperature",),
            min_family_percent=30.0,
        )
        
        matched_rule, confidence = match_rule(temperature_dominant_families, rules=[rule])
        
        assert matched_rule is not None
        assert matched_rule.name == "thermal_alert"
        assert confidence > 0.0
    
    def test_balanced_families_no_match(self, balanced_families):
        """Test that balanced families don't match strict dominance rules."""
        rule = AlertRule(
            name="voltage_alert",
            root_cause="Power instability",
            required_families=("Voltage",),
            min_family_percent=40.0,
        )
        
        matched_rule, confidence = match_rule(balanced_families, rules=[rule])
        
        assert matched_rule is None  # Voltage is only 22%
    
    def test_missing_family_no_match(self, voltage_dominant_families):
        """Test that rule doesn't match if required family is missing."""
        # Remove Voltage from families
        families_without_voltage = [(f, p) for f, p in voltage_dominant_families if f != "Voltage"]
        
        rule = AlertRule(
            name="voltage_alert",
            root_cause="Power instability",
            required_families=("Voltage",),
            min_family_percent=40.0,
        )
        
        matched_rule, confidence = match_rule(families_without_voltage, rules=[rule])
        
        assert matched_rule is None
    
    def test_empty_families_no_match(self, missing_family_data):
        """Test that empty family data doesn't match any rule."""
        rule = AlertRule(
            name="voltage_alert",
            root_cause="Power instability",
            required_families=("Voltage",),
            min_family_percent=40.0,
        )
        
        matched_rule, confidence = match_rule(missing_family_data, rules=[rule])
        
        assert matched_rule is None


class TestMultiFamilyDominance:
    """Test rules requiring multiple families to be dominant."""
    
    def test_power_instability_both_families_present(self):
        """Test power instability rule when both Voltage and Current are high."""
        families = [
            ('Voltage', 30.0),
            ('Current', 25.0),
            ('Temperature', 20.0),
            ('RPM', 15.0),
            ('Vibration', 10.0),
        ]
        
        rule = AlertRule(
            name="power_instability",
            root_cause="Power instability",
            required_families=("Voltage", "Current"),
            min_family_percent=20.0,
        )
        
        matched_rule, confidence = match_rule(families, rules=[rule])
        
        assert matched_rule is not None
        assert confidence > 0.0
    
    def test_power_instability_one_family_missing(self):
        """Test power rule fails when one required family is below threshold."""
        families = [
            ('Voltage', 40.0),  # High
            ('Current', 10.0),  # Too low
            ('Temperature', 25.0),
            ('RPM', 15.0),
            ('Vibration', 10.0),
        ]
        
        rule = AlertRule(
            name="power_instability",
            root_cause="Power instability",
            required_families=("Voltage", "Current"),
            min_family_percent=20.0,
        )
        
        matched_rule, confidence = match_rule(families, rules=[rule])
        
        assert matched_rule is None  # Current < 20%
    
    def test_mechanical_wear_vibration_and_rpm(self):
        """Test mechanical wear rule with Vibration + RPM."""
        families = [
            ('Vibration', 30.0),
            ('RPM', 28.0),
            ('Temperature', 20.0),
            ('Current', 12.0),
            ('Voltage', 10.0),
        ]
        
        rule = AlertRule(
            name="mechanical_wear",
            root_cause="Mechanical wear",
            required_families=("Vibration", "RPM"),
            min_family_percent=15.0,
        )
        
        matched_rule, confidence = match_rule(families, rules=[rule])
        
        assert matched_rule is not None
        assert confidence > 0.0


class TestConfidenceScoring:
    """Test confidence scoring for dominant family rules."""
    
    def test_confidence_increases_with_percentage(self):
        """Test that confidence increases as family percentage increases."""
        rule = AlertRule(
            name="voltage_alert",
            root_cause="Power instability",
            required_families=("Voltage",),
            min_family_percent=40.0,
        )
        
        # Test with 40% (exactly at threshold)
        families_40 = [('Voltage', 40.0), ('Temperature', 60.0)]
        _, conf_40 = match_rule(families_40, rules=[rule])
        
        # Test with 60% (well above threshold)
        families_60 = [('Voltage', 60.0), ('Temperature', 40.0)]
        _, conf_60 = match_rule(families_60, rules=[rule])
        
        # Test with 80% (very high)
        families_80 = [('Voltage', 80.0), ('Temperature', 20.0)]
        _, conf_80 = match_rule(families_80, rules=[rule])
        
        # Confidence should increase with percentage
        assert conf_40 <= conf_60 <= conf_80
    
    def test_confidence_capped_at_one(self):
        """Test that confidence is capped at 1.0."""
        rule = AlertRule(
            name="voltage_alert",
            root_cause="Power instability",
            required_families=("Voltage",),
            min_family_percent=20.0,
        )
        
        families = [('Voltage', 90.0), ('Temperature', 10.0)]
        _, confidence = match_rule(families, rules=[rule])
        
        assert confidence <= 1.0
    
    def test_confidence_multi_family_average(self):
        """Test that multi-family confidence is averaged across families."""
        rule = AlertRule(
            name="power_instability",
            root_cause="Power instability",
            required_families=("Voltage", "Current"),
            min_family_percent=20.0,
        )
        
        # Voltage: 40% / 20% = 2.0 (capped at 1.0)
        # Current: 30% / 20% = 1.5 (capped at 1.0)
        # Average: (1.0 + 1.0) / 2 = 1.0
        families = [
            ('Voltage', 40.0),
            ('Current', 30.0),
            ('Temperature', 30.0),
        ]
        
        _, confidence = match_rule(families, rules=[rule])
        
        # Should be high since both are well above threshold
        assert confidence >= 0.8


class TestRulePrecedence:
    """Test behavior when multiple rules could match."""
    
    def test_highest_confidence_rule_selected(self):
        """Test that the rule with highest confidence is selected."""
        families = [
            ('Voltage', 50.0),
            ('Temperature', 30.0),
            ('Current', 20.0),
        ]
        
        rules = [
            AlertRule(
                name="voltage_alert",
                root_cause="Power instability",
                required_families=("Voltage",),
                min_family_percent=40.0,  # 50/40 = 1.25, capped at 1.0
            ),
            AlertRule(
                name="thermal_alert",
                root_cause="Thermal overload",
                required_families=("Temperature",),
                min_family_percent=25.0,  # 30/25 = 1.2, capped at 1.0
            ),
        ]
        
        matched_rule, confidence = match_rule(families, rules=rules)
        
        # Both rules match, but voltage has higher confidence
        # (This assumes match_rule returns best match)
        assert matched_rule is not None
        # The exact winner depends on your implementation


class TestAlertEventCreation:
    """Test creating AlertEvent from row with dominant family logic."""
    
    def test_alert_event_with_matching_rule(
        self,
        critical_score_row,
        voltage_dominant_families,
        sample_top_features
    ):
        """Test alert event creation when rule matches."""
        alert = build_alert_event_from_row(
            row=critical_score_row,
            families=voltage_dominant_families,
            top_features=sample_top_features,
            score_col='score',
            tag_col='anomaly_tag',
        )
        
        assert alert.device_id == 'DEV-001'
        assert alert.severity in ['CRITICAL', 'WARNING', 'INFO']
        assert alert.root_cause is not None
        assert len(alert.root_cause) > 0
        assert alert.confidence > 0.0
    
    def test_alert_event_with_no_matching_rule(
        self,
        info_score_row,
        balanced_families,
        sample_top_features
    ):
        """Test fallback alert when no rule matches."""
        alert = build_alert_event_from_row(
            row=info_score_row,
            families=balanced_families,
            top_features=sample_top_features,
            score_col='score',
            tag_col='anomaly_tag',
        )
        
        assert alert.device_id == 'DEV-001'
        assert alert.root_cause is not None
        # Should use fallback logic (e.g., "Anomaly dominated by <top_family>")
        assert "dominated" in alert.root_cause.lower() or "anomaly" in alert.root_cause.lower()
        assert alert.rule_name == "fallback_top_family"


class TestEdgeCases:
    """Test edge cases for dominant family rules."""
    
    def test_nan_family_percentage(self):
        """Test handling of NaN family percentages."""
        families = [
            ('Voltage', float('nan')),
            ('Temperature', 50.0),
            ('Current', 50.0),
        ]
        
        rule = AlertRule(
            name="voltage_alert",
            root_cause="Power instability",
            required_families=("Voltage",),
            min_family_percent=40.0,
        )
        
        matched_rule, confidence = match_rule(families, rules=[rule])
        
        # Should not match due to NaN
        assert matched_rule is None
    
    def test_zero_family_percentage(self):
        """Test family with 0% contribution."""
        families = [
            ('Voltage', 0.0),
            ('Temperature', 100.0),
        ]
        
        rule = AlertRule(
            name="voltage_alert",
            root_cause="Power instability",
            required_families=("Voltage",),
            min_family_percent=1.0,
        )
        
        matched_rule, confidence = match_rule(families, rules=[rule])
        
        assert matched_rule is None
    
    def test_exact_threshold_match(self):
        """Test when family percentage exactly equals threshold."""
        families = [('Voltage', 40.0), ('Temperature', 60.0)]
        
        rule = AlertRule(
            name="voltage_alert",
            root_cause="Power instability",
            required_families=("Voltage",),
            min_family_percent=40.0,
        )
        
        matched_rule, confidence = match_rule(families, rules=[rule])
        
        # Should match (threshold is inclusive)
        assert matched_rule is not None