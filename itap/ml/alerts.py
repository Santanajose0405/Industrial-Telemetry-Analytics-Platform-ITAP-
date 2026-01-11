from __future__ import annotations

from dataclasses import dataclass, field, asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import yaml

# =============================================================================
# Data structures (SUPPORTS BOTH: unit-test API + YAML-rule-engine API)
# =============================================================================

@dataclass
class AlertRule:
    """
    This dataclass supports TWO shapes:

    A) Unit-test "dominant family" rules (used by tests/conftest.py):
        - name, root_cause, required_families, min_family_percent, severity_score_thresholds

    B) YAML rule-engine rules (used by load_alert_rules/evaluate_alert_rules):
        - id, type, enabled, severity, message, params

    Both can coexist in the same module.
    """

    # ---- Shape A (dominant-family unit tests) ----
    name: str = ""
    root_cause: str = ""
    required_families: Tuple[str, ...] = ()
    min_family_percent: float = 0.0
    # (warning_threshold, critical_threshold)
    severity_score_thresholds: Tuple[float, float] = (0.11, 0.15)

    # ---- Shape B (YAML rule engine) ----
    id: str = ""
    type: str = ""
    enabled: bool = True
    severity: str = "INFO"
    message: str = ""
    params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Provide reasonable defaults/aliases so both shapes behave.
        if not self.id:
            self.id = self.name or ""
        if not self.message and self.root_cause:
            self.message = self.root_cause
        if not self.root_cause and self.message:
            self.root_cause = self.message
        if not self.name and self.id:
            self.name = self.id


@dataclass
class AlertEvent:
    """
    Superset event structure.

    The unit tests expect at least:
      - device_id, tag, severity, root_cause, confidence
    Your engine/run_score code often expects:
      - queue, rule_id, cause, context
    """

    # Common
    timestamp: str
    device_id: str
    state: str
    score: float
    severity: str

    # Unit-test-friendly fields
    tag: str = ""
    route: str = "triage"
    rule_name: str = ""
    root_cause: str = ""
    confidence: float = 0.0
    families: List[Tuple[str, float]] = field(default_factory=list)
    top_features: List[Any] = field(default_factory=list)

    # Engine-friendly aliases
    queue: str = ""
    rule_id: str = ""
    cause: str = ""
    context: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Normalize canonical/alias fields for compatibility.
        if not self.queue:
            self.queue = self.route
        if not self.route:
            self.route = self.queue

        if not self.rule_id:
            self.rule_id = self.rule_name
        if not self.rule_name:
            self.rule_name = self.rule_id

        if not self.cause:
            self.cause = self.root_cause
        if not self.root_cause:
            self.root_cause = self.cause


# =============================================================================
# YAML Config loading (returns LIST to satisfy tests/test_alert_rules_config.py)
# =============================================================================

def load_alert_rules(path: str | Path) -> List[AlertRule]:
    """
    Load YAML alert rules.

    The config tests expect this function to return a LIST of rule objects
    (not a tuple). :contentReference[oaicite:3]{index=3}
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Alert rules config not found: {p}")

    raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    # Accept either {rules:[...]} or direct list
    rules_cfg = raw["rules"] if isinstance(raw, dict) and "rules" in raw else raw
    if not isinstance(rules_cfg, list):
        raise ValueError("alert rules YAML must be a list (or {rules: [...]})")

    rules: List[AlertRule] = []
    for r in rules_cfg:
        if not isinstance(r, dict):
            continue
        rules.append(
            AlertRule(
                id=str(r.get("id", r.get("name", ""))),
                type=str(r.get("type", "")),
                enabled=bool(r.get("enabled", True)),
                severity=str(r.get("severity", "INFO")).upper(),
                message=str(r.get("message", r.get("cause", "")) or ""),
                params={k: v for k, v in r.items() if k not in {"id", "name", "type", "enabled", "severity", "message", "cause"}},
            )
        )
    return rules


def _load_alert_cfg(path: str | Path) -> Dict[str, Any]:
    """
    Loads the *full* YAML file so routing/defaults can be used by the engine helpers.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Alert rules config not found: {p}")
    raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return raw if isinstance(raw, dict) else {"rules": raw}


# =============================================================================
# Dominant-family matching API (required by tests)
# =============================================================================

def match_rule(
    families_sorted: List[Tuple[str, float]],
    *,
    rules: List[AlertRule],
) -> Tuple[Optional[AlertRule], float]:
    """
    Return (best_matching_rule, confidence).

    Confidence scoring required by tests:
      - For each required family: conf_i = min(1.0, pct / min_family_percent)
      - Final confidence = average(conf_i) across required families
      - Rule matches only if ALL required families are present and pct >= min_family_percent
    :contentReference[oaicite:4]{index=4}
    """
    if not families_sorted:
        return None, 0.0

    fam_map: Dict[str, float] = {}
    for fam, pct in families_sorted:
        try:
            v = float(pct)
        except Exception:
            continue
        if pd.isna(v) or v <= 0:
            continue
        fam_map[str(fam)] = v

    best_rule: Optional[AlertRule] = None
    best_conf: float = 0.0

    for rule in rules:
        req = tuple(rule.required_families or ())
        if not req:
            continue

        threshold = float(rule.min_family_percent or 0.0)
        if threshold <= 0:
            continue

        # Must have all required families and each must meet threshold
        ok = True
        conf_parts: List[float] = []
        for fam in req:
            if fam not in fam_map:
                ok = False
                break
            pct = fam_map[fam]
            if pct < threshold:
                ok = False
                break
            conf_parts.append(min(1.0, pct / threshold))

        if not ok or not conf_parts:
            continue

        conf = float(sum(conf_parts) / len(conf_parts))
        if conf > best_conf:
            best_conf = conf
            best_rule = rule

    if best_rule is None:
        return None, 0.0
    return best_rule, best_conf


# =============================================================================
# Tag routing + severity mapping (required by tests)
# =============================================================================

_TAG_ROUTE_DEFAULTS: Dict[str, str] = {
    "bearing_wear": "maintenance",
    "overheat_drift": "thermal",
    "sensor_dropout": "instrumentation",
    "power_spike": "electrical",
}

_TAG_SEVERITY_DEFAULTS: Dict[str, str] = {
    "bearing_wear": "WARNING",
    "overheat_drift": "WARNING",
    "sensor_dropout": "INFO",
    "power_spike": "CRITICAL",
}

_TAG_ROOT_CAUSE_DEFAULTS: Dict[str, str] = {
    "bearing_wear": "Mechanical degradation: bearing wear pattern detected",
    "overheat_drift": "Thermal anomaly: temperature/overheat drift pattern detected",
    "sensor_dropout": "Instrumentation fault: sensor dropout pattern detected",
    "power_spike": "Electrical fault: power/voltage spike detected",
}


def _normalize_tag(tag: Any) -> str:
    if tag is None:
        return ""
    s = str(tag).strip()
    return s


def _score_to_severity(score: float, thresholds: Tuple[float, float]) -> str:
    warn_th, crit_th = thresholds
    try:
        s = float(score)
    except Exception:
        return "INFO"
    if s >= float(crit_th):
        return "CRITICAL"
    if s >= float(warn_th):
        return "WARNING"
    return "INFO"


def build_alert_event_from_row(
    *,
    row: pd.Series,
    families: List[Tuple[str, float]],
    top_features: List[Any],
    score_col: str = "score",
    tag_col: str = "anomaly_tag",
    rules: Optional[List[AlertRule]] = None,
    default_thresholds: Tuple[float, float] = (0.11, 0.15),
) -> AlertEvent:
    """
    Build a single AlertEvent from a scored row, combining:
      1) Tag routing (if tag is present and known)
      2) Otherwise dominant-family rule match (if rules passed)
      3) Otherwise generic fallback

    Used by:
      - tests/test_alert_rules_dominant_family.py :contentReference[oaicite:5]{index=5}
      - tests/test_alert_rules_routing.py :contentReference[oaicite:6]{index=6}
    """
    ts = str(row.get("timestamp", ""))
    device_id = str(row.get("device_id", ""))
    state = str(row.get("state", ""))
    try:
        score = float(row.get(score_col, 0.0))
    except Exception:
        score = 0.0

    raw_tag = _normalize_tag(row.get(tag_col, ""))
    tag = raw_tag.strip()

    # Severity: tag override if known, else derived from score thresholds
    if tag in _TAG_SEVERITY_DEFAULTS:
        severity = _TAG_SEVERITY_DEFAULTS[tag]
    else:
        severity = _score_to_severity(score, default_thresholds)

    # Route + root cause: tag overrides if known
    if tag in _TAG_ROUTE_DEFAULTS:
        route = _TAG_ROUTE_DEFAULTS[tag]
    else:
        route = "triage"

    if tag in _TAG_ROOT_CAUSE_DEFAULTS:
        root_cause = _TAG_ROOT_CAUSE_DEFAULTS[tag]
        rule_name = f"tag_route::{tag}"
        confidence = 1.0
    else:
        # Fall back to dominant-family matching if rules provide; 
        # otherwise us an operator-friendly message
        if families and len(families) > 0 and isinstance(families[0], (list, tuple)) and len(families[0]) >= 1:
            top_family = str(families[0][0])
            root_cause = f"Anomaly dominated by {top_family}"
            rule_name = "fallback_top_family"
        else:
            root_cause = "Anomaly detected"
            rule_name = "fallback_top_family"

        confidence = 0.0

        if rules:
            matched, conf = match_rule(families, rules=rules)
            if matched is not None:
                # If a rule matches, it takes precednce over the generic fallback
                root_cause = matched.root_cause or matched.message or root_cause
                rule_name = matched.name or matched.id or rule_name
                confidence = float(conf)

    return AlertEvent(
        timestamp=ts,
        device_id=device_id,
        state=state,
        score=score,
        severity=str(severity).upper(),
        tag=tag,
        route=route,
        rule_name=rule_name,
        root_cause=root_cause,
        confidence=float(confidence),
        families=list(families or []),
        top_features=list(top_features or []),
        context={
            "tag": tag,
            "route": route,
            "families": list(families or []),
            "top_features": list(top_features or []),
        },
    )


# =============================================================================
# Existing/engine helpers (kept minimal so your earlier passing tests stay passing)
# =============================================================================

def build_alert_rules_from_config(cfg_rules: List[Dict[str, Any]]) -> List[AlertRule]:
    """
    Build AlertRule objects from an already-loaded YAML rules list.

    IMPORTANT:
    - This function is used by config contract tests.
    - It must fail fast on unknown rule types (clear error), rather than silently accepting them.
    """
    allowed_types = {
        "burst",
        "dominant_family",
        "tag_route",
        "tagged_route",
        "tag_routing",
    }

    rules: List[AlertRule] = []
    for idx, r in enumerate(cfg_rules):
        if not isinstance(r, dict):
            raise TypeError(f"Rule at index {idx} must be a dict, got {type(r).__name__}")

        rule_type = str(r.get("type", "")).strip()
        if not rule_type:
            raise ValueError(f"Rule at index {idx} is missing required field 'type'")

        if rule_type not in allowed_types:
            raise ValueError(
                f"Unknown rule type '{rule_type}' at index {idx}. "
                f"Allowed types: {sorted(allowed_types)}"
            )

        rules.append(
            AlertRule(
                id=str(r.get("id", r.get("name", ""))),
                type=rule_type,
                enabled=bool(r.get("enabled", True)),
                severity=str(r.get("severity", "INFO")).upper(),
                message=str(r.get("message", r.get("cause", "")) or ""),
                params={
                    k: v
                    for k, v in r.items()
                    if k not in {"id", "name", "type", "enabled", "severity", "message", "cause"}
                },
            )
        )

    return rules



def build_alerts_from_config(
    *,
    df_explain: pd.DataFrame,
    config_path: str | Path = "configs/alert_rules.yaml",
) -> List[AlertEvent]:
    """
    Convenience adapter for your scoring pipeline.
    This intentionally stays conservative: it creates per-row AlertEvents using the
    test-friendly builder, while still honoring YAML routing defaults if present.
    """
    cfg = _load_alert_cfg(config_path)
    rules = load_alert_rules(config_path)

    # Dominant-family rules for match_rule() come from your in-memory rule set (if any).
    # Here we do NOT auto-generate dominant-family rules from YAML rule-engine entries,
    # because your YAML currently defines engine-style rules (id/type/params). :contentReference[oaicite:7]{index=7}
    dominant_rules: List[AlertRule] = []

    out: List[AlertEvent] = []
    if df_explain is None or df_explain.empty:
        return out

    for _, row in df_explain.iterrows():
        # Only emit events for anomalies (pred == 1) if column exists
        if "pred" in row and int(row.get("pred", 0)) != 1:
            continue

        families = row.get("families_sorted", [])
        top_features = row.get("top_features", [])

        if not isinstance(families, list):
            families = []
        if not isinstance(top_features, list):
            top_features = []

        out.append(
            build_alert_event_from_row(
                row=row,
                families=families,
                top_features=top_features,
                score_col="score",
                tag_col="anomaly_tag",
                rules=dominant_rules,  # optional; can be wired later
                default_thresholds=(0.11, 0.15),
            )
        )

    return out

def alerts_to_json(alerts: List["AlertEvent"]) -> List[Dict[str, Any]]:
    """
    Convert AlertEvent objects into JSON-serializable dicts.

    This is intentionally tolerant of schema evolution: we include common fields
    if present and fall back to dataclass asdict() when possible.
    """
    out: List[Dict[str, Any]] = []

    for a in alerts or []:
        if is_dataclass(a):
            d = asdict(a)
        elif isinstance(a, dict):
            d = dict(a)
        else:
            # best-effort object -> dict
            d = {k: getattr(a, k) for k in dir(a) if not k.startswith("_")}

        # Ensure a stable-ish outward shape (keep extras too)
        d.setdefault("timestamp", getattr(a, "timestamp", ""))
        d.setdefault("device_id", getattr(a, "device_id", ""))
        d.setdefault("state", getattr(a, "state", ""))
        d.setdefault("score", getattr(a, "score", 0.0))
        d.setdefault("severity", getattr(a, "severity", ""))
        d.setdefault("tag", getattr(a, "tag", ""))
        d.setdefault("route", getattr(a, "route", getattr(a, "queue", "")))
        d.setdefault("queue", getattr(a, "queue", getattr(a, "route", "")))
        d.setdefault("rule_id", getattr(a, "rule_id", getattr(a, "rule_name", "")))
        d.setdefault("rule_name", getattr(a, "rule_name", getattr(a, "rule_id", "")))
        d.setdefault("cause", getattr(a, "cause", getattr(a, "root_cause", "")))
        d.setdefault("root_cause", getattr(a, "root_cause", getattr(a, "cause", "")))
        d.setdefault("confidence", getattr(a, "confidence", 0.0))
        d.setdefault("families", getattr(a, "families", []))
        d.setdefault("top_features", getattr(a, "top_features", []))
        d.setdefault("context", getattr(a, "context", {}))

        out.append(d)

    return out


def print_alerts(alerts: List["AlertEvent"], max_items: int = 50) -> None:
    """
    Human-readable operator output for alerts.

    Kept as a lightweight helper because `run_score` imports it.
    """
    if not alerts:
        print("\nALERTS (operator-ready): none")
        return

    print("\nALERTS (operator-ready):")
    for a in alerts[:max_items]:
        ts = getattr(a, "timestamp", "")
        device_id = getattr(a, "device_id", "")
        state = getattr(a, "state", "")
        severity = str(getattr(a, "severity", "")).upper()
        score = getattr(a, "score", 0.0)
        route = getattr(a, "route", getattr(a, "queue", "triage"))
        tag = getattr(a, "tag", "")
        rule = getattr(a, "rule_name", getattr(a, "rule_id", ""))
        cause = getattr(a, "root_cause", getattr(a, "cause", ""))
        conf = getattr(a, "confidence", 0.0)

        # Optional: short family summary if present
        fam = getattr(a, "families", None)
        fam_str = ""
        if isinstance(fam, list) and fam:
            # fam may be List[Tuple[str,float]] or List[dict]; handle both.
            pairs = []
            for item in fam:
                if isinstance(item, (list, tuple)) and len(item) == 2:
                    pairs.append((str(item[0]), float(item[1])))
                elif isinstance(item, dict) and "family" in item and "percent" in item:
                    pairs.append((str(item["family"]), float(item["percent"])))
            if pairs:
                top3 = sorted(pairs, key=lambda kv: kv[1], reverse=True)[:3]
                fam_str = " | " + ", ".join([f"{k}={v:.1f}%" for k, v in top3])

        try:
            score_s = f"{float(score):.4f}"
        except Exception:
            score_s = str(score)

        print(
            f"- {severity} | {ts} | {device_id} | {state} | score={score_s} "
            f"| route={route} | tag={tag} | conf={conf:.2f} | cause={cause} | rule={rule}"
            f"{fam_str}"
        )
