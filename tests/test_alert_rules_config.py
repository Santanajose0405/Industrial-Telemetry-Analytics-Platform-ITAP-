from __future__ import annotations

from pathlib import Path

import pytest
import yaml


def _load_yaml(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_alert_rules_yaml_exists_and_parses():
    """
    The repo should include configs/alert_rules.yaml and it should parse as YAML.

    This test intentionally validates the *data contract* for operator rules,
    not the alert engine implementation.
    """
    path = Path("configs") / "alert_rules.yaml"
    assert path.exists(), "Expected configs/alert_rules.yaml to exist"

    raw = _load_yaml(path)
    assert raw is not None, "alert_rules.yaml parsed to None (empty file?)"

    # Common shapes: list[rule] OR {rules: [...]}.
    if isinstance(raw, dict) and "rules" in raw:
        rules = raw["rules"]
    else:
        rules = raw

    assert isinstance(rules, list), "alert_rules.yaml should be a list of rule objects (or {rules: [...]})"
    assert len(rules) >= 1, "alert_rules.yaml should define at least one rule"

    # Minimal required keys per rule
    for r in rules:
        assert isinstance(r, dict), "Each rule must be a mapping/object"
        assert "name" in r and isinstance(r["name"], str) and r["name"].strip()
        assert "type" in r and isinstance(r["type"], str) and r["type"].strip()


def test_alert_rules_required_fields_by_type():
    """
    Validate the schema expectations by rule type.

    This protects you from drifting config formats during refactors.
    """
    path = Path("configs") / "alert_rules.yaml"
    raw = _load_yaml(path)
    rules = raw["rules"] if isinstance(raw, dict) and "rules" in raw else raw

    # Define "required fields per type" for your three operator-ready rules.
    required = {
        "burst": {"device_window_minutes", "min_anomalies"},
        "dominant_family": {"family", "min_percent"},
        "tag_route": {"tag", "route"},
    }

    # Optional fields you likely include, but do not strictly require.
    # (You can tighten these later.)
    for r in rules:
        rtype = r.get("type")
        if rtype not in required:
            # If you add new types later, update the required map.
            continue

        missing = sorted(list(required[rtype] - set(r.keys())))
        assert not missing, f"Rule '{r.get('name')}' of type '{rtype}' missing required fields: {missing}"


def test_alert_engine_can_load_rules():
    """
    Ensure your alert engine can load and interpret the rules.

    Adjust the import/function names to match your actual implementation.
    """
    # Lazy import inside test so config-only tests still run if implementation moves.
    import itap.ml.alerts as alerts

    path = Path("configs") / "alert_rules.yaml"

    # Try common API shapes.
    rules = None

    if hasattr(alerts, "load_alert_rules"):
        rules = alerts.load_alert_rules(path)
    elif hasattr(alerts, "build_alert_rules_from_config"):
        raw = _load_yaml(path)
        cfg = raw["rules"] if isinstance(raw, dict) and "rules" in raw else raw
        rules = alerts.build_alert_rules_from_config(cfg)

    assert rules is not None, (
        "Could not find a rules loader in itap.ml.alerts. "
        "Expected load_alert_rules(...) or build_alert_rules_from_config(...)."
    )

    assert isinstance(rules, list), "Alert engine should return a list of rule objects"
    assert len(rules) >= 1, "Alert engine returned no rules"


def test_alert_engine_rejects_unknown_rule_type():
    """
    A bad rule type should fail fast (clear error), rather than silently doing nothing.
    """
    import itap.ml.alerts as alerts

    bad_rule = {"name": "bad", "type": "definitely_not_real"}

    if hasattr(alerts, "build_alert_rules_from_config"):
        with pytest.raises(Exception):
            alerts.build_alert_rules_from_config([bad_rule])
    elif hasattr(alerts, "load_alert_rules"):
        # If your loader reads from a file only, we can still validate via helper:
        # Many implementations expose a lower-level parse/validate function.
        if hasattr(alerts, "validate_rule_config"):
            with pytest.raises(Exception):
                alerts.validate_rule_config(bad_rule)
        else:
            pytest.skip("No build_alert_rules_from_config or validate_rule_config function available.")
    else:
        pytest.skip("No recognizable alert rule loader API found.")
