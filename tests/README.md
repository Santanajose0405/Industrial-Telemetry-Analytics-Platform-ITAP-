# Alert Rules Unit Tests

Comprehensive test suite for the ITAP alert rules system.

## 📋 Test Structure

```
tests/
├── conftest.py                              # Shared fixtures
├── test_alert_rules_config.py              # Rule configuration & validation
├── test_alert_rules_dominant_family.py     # Dominant family rules
├── test_alert_rules_burst.py               # Burst detection rules
├── test_alert_rules_routing.py             # Tag-based routing rules
└── README.md                                # This file
```

## 🎯 Test Coverage

### 1. Configuration Tests (`test_alert_rules_config.py`)
- ✅ AlertRule dataclass creation and validation
- ✅ DEFAULT_RULES consistency
- ✅ Rule configuration best practices
- ✅ YAML config loading (when implemented)

### 2. Dominant Family Tests (`test_alert_rules_dominant_family.py`)
- ✅ Family dominance matching logic
- ✅ Multi-family rules (e.g., Voltage + Current)
- ✅ Confidence scoring
- ✅ Rule precedence
- ✅ AlertEvent creation
- ✅ Edge cases (NaN, zero, exact thresholds)

### 3. Burst Detection Tests (`test_alert_rules_burst.py`)
- ✅ Basic burst detection (N events in M minutes)
- ✅ Time window boundaries (inclusive/exclusive)
- ✅ Sliding window behavior
- ✅ Per-device isolation
- ✅ Minimum anomaly thresholds
- ✅ Deduplication logic
- ✅ Edge cases

### 4. Tag Routing Tests (`test_alert_rules_routing.py`)
- ✅ Basic tag-to-route mapping
- ✅ Untagged event handling
- ✅ Tag normalization (case, whitespace)
- ✅ Unknown tag fallback
- ✅ Severity and root cause mapping
- ✅ Batch routing
- ✅ Edge cases

## 🚀 Running Tests

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test File
```bash
pytest tests/test_alert_rules_config.py -v
pytest tests/test_alert_rules_dominant_family.py -v
pytest tests/test_alert_rules_burst.py -v
pytest tests/test_alert_rules_routing.py -v
```

### Run Specific Test Class
```bash
pytest tests/test_alert_rules_config.py::TestAlertRuleDataclass -v
pytest tests/test_alert_rules_dominant_family.py::TestDominantFamilyMatching -v
```

### Run Specific Test
```bash
pytest tests/test_alert_rules_config.py::TestAlertRuleDataclass::test_alert_rule_creation_minimal -v
```

### Run with Coverage
```bash
pytest tests/ --cov=itap.ml.alerts --cov-report=html
```

### Run Only Fast Tests (skip slow ones)
```bash
pytest tests/ -m "not slow"
```

## 📊 Test Fixtures

All fixtures are defined in `conftest.py` for reusability:

### Time Fixtures
- `base_timestamp` - Base time for all tests
- `timestamps_within_window` - Events within 15min window
- `timestamps_outside_window` - Events outside window
- `timestamps_exact_boundary` - Events at exact boundary

### Family Fixtures
- `voltage_dominant_families` - Voltage > 45%
- `temperature_dominant_families` - Temperature > 28%
- `vibration_rpm_dominant_families` - Mechanical wear pattern
- `balanced_families` - No clear dominance
- `missing_family_data` - Empty/incomplete data

### Event Fixtures
- `single_device_events` - 3 events, same device, within window
- `multi_device_events` - 3 events, different devices
- `sparse_events` - Events too far apart
- `tagged_events` - Events with various tags

### Rule Fixtures
- `burst_rule_config` - Burst rule configuration
- `dominant_family_rule_config` - Family rule config
- `tag_route_rule_config` - Routing rule config
- `sample_alert_rules` - AlertRule objects

### Score Fixtures
- `critical_score_row` - score >= 0.15 (critical)
- `warning_score_row` - 0.11 <= score < 0.15 (warning)
- `info_score_row` - score < 0.11 (info)

## 🔧 Implementation TODOs

Some tests are marked with `@pytest.mark.skip` because the corresponding functionality needs to be implemented:

### High Priority
1. **Burst detection function** (`evaluate_burst_rule()`)
   - Input: DataFrame with events
   - Output: List of AlertEvent objects
   - Logic: Sliding window, per-device, deduplication

2. **YAML rule loader** (`load_alert_rules()`)
   - Input: Path to YAML config
   - Output: List of AlertRule objects
   - Validation: Schema, required fields, thresholds

3. **Rule evaluation API** (`evaluate_alerts()`)
   - Input: Events DataFrame, list of rules
   - Output: List of AlertEvent objects
   - Logic: Apply all rules, handle precedence

### Medium Priority
4. **Alert deduplication**
   - Prevent duplicate alerts for same burst
   - Cooldown periods
   - Grouping logic

5. **Route field in AlertEvent**
   - Add `route: str` field to AlertEvent dataclass
   - Populate based on tag routing rules

## 🎯 Critical Decisions to Lock In

### Time Window Boundaries (Burst Rules)
**Decision Required:** Are events at exactly M minutes apart INCLUSIVE or EXCLUSIVE?

Example: Events at t+0, t+15, t+30 with 15-minute window
- **INCLUSIVE**: t+15 and t+30 are within same window ✓
- **EXCLUSIVE**: t+15 and t+30 are NOT in same window

**Recommendation:** INCLUSIVE (more operator-friendly)

**Test:** `test_events_exactly_at_boundary_inclusive()`

### Deduplication Strategy (Burst Rules)
**Decision Required:** How to prevent duplicate alerts for overlapping bursts?

Options:
1. **Cooldown period**: No new alerts for X minutes after burst
2. **Window grouping**: One alert per burst window
3. **Flag tracking**: Mark events as "alerted" 

**Recommendation:** Window grouping (clearest for operators)

**Test:** `test_no_duplicate_alerts_for_same_burst()`

### Rule Precedence (Multiple Matches)
**Decision Required:** What happens when multiple rules match?

Options:
1. **Highest confidence wins**: Return single best match
2. **All matches**: Return multiple alerts
3. **Priority order**: First matching rule wins

**Recommendation:** Highest confidence wins (reduces noise)

**Test:** `test_highest_confidence_rule_selected()`

## 📝 Test Writing Guidelines

### 1. Test Names Should Be Descriptive
```python
# ✅ Good
def test_voltage_dominance_matches_when_above_threshold():
    pass

# ❌ Bad
def test_voltage():
    pass
```

### 2. Use Fixtures for Reusability
```python
# ✅ Good
def test_burst_detection(single_device_events):
    df = single_device_events
    # Test logic

# ❌ Bad (duplicates fixture logic)
def test_burst_detection():
    df = pd.DataFrame({...})  # Repeated setup
    # Test logic
```

### 3. Test One Thing Per Test
```python
# ✅ Good
def test_burst_triggers_with_three_events():
    # Test only burst triggering
    
def test_burst_includes_event_count():
    # Test only event count in alert

# ❌ Bad
def test_burst_everything():
    # Tests triggering, content, dedup all at once
```

### 4. Assert Behavior, Not Implementation
```python
# ✅ Good
assert matched_rule is not None  # Tests outcome
assert confidence > 0.0

# ❌ Bad (tests implementation details)
assert rule._internal_counter == 3
```

### 5. Include Edge Cases
```python
def test_zero_family_percentage():
    # Edge case: 0% contribution
    
def test_nan_family_percentage():
    # Edge case: NaN values
    
def test_exact_threshold_match():
    # Edge case: Exactly at boundary
```

## 🐛 Debugging Failed Tests

### View Detailed Output
```bash
pytest tests/ -v -s
```

### Run Specific Failed Test
```bash
pytest tests/test_alert_rules_burst.py::TestTimeWindowBoundaries::test_events_exactly_at_boundary_inclusive -v
```

### Drop into Debugger on Failure
```bash
pytest tests/ --pdb
```

### Show Local Variables on Failure
```bash
pytest tests/ -l
```

## 📈 Coverage Goals

Target coverage for alert rules:
- Overall: **>90%**
- Critical paths (burst detection, family matching): **100%**
- Edge cases: **>80%**

Check coverage:
```bash
pytest tests/ --cov=itap.ml.alerts --cov-report=term-missing
```

## 🔗 Related Documentation

- [alerts.py](../itap/ml/alerts.py) - Alert rules implementation
- [aggregate.py](../itap/ml/aggregate.py) - Alert aggregation
- [explain.py](../itap/ml/explain.py) - Explainability logic
- [configs/alert_rules.yaml](../configs/alert_rules.yaml) - Rule configuration

## ✅ Test Checklist

Before merging alert rules code:

- [ ] All tests pass
- [ ] Coverage >90% for alert rules
- [ ] Time boundary behavior locked in
- [ ] Deduplication strategy implemented and tested
- [ ] Rule precedence logic defined and tested
- [ ] Edge cases covered (NaN, empty, zero, null)
- [ ] Burst detection tested across devices
- [ ] Tag routing tested with unknown tags
- [ ] Documentation updated

## 🤝 Contributing Tests

When adding new alert rule types:

1. Add fixtures to `conftest.py`
2. Create new test file (e.g., `test_alert_rules_newtype.py`)
3. Test happy path, edge cases, and error conditions
4. Update this README with coverage info
5. Ensure >90% coverage for new code