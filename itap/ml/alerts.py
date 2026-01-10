from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class AlertRule:
    name: str
    root_cause: str
    required_families: Tuple[str, ...]
    min_family_percent: float = 20.0
    severity_score_thresholds: Tuple[float, float] = (0.11, 0.15)  # (warn, critical)


@dataclass
class AlertEvent:
    timestamp: str
    device_id: str
    state: str
    score: float
    severity: str
    root_cause: str
    confidence: float
    families: List[Tuple[str, float]]
    top_features: List[Tuple[str, float]]
    tag: str = ""
    rule_name: str = ""


DEFAULT_RULES: List[AlertRule] = [
    AlertRule(
        name="power_instability_voltage_current",
        root_cause="Power instability",
        required_families=("Voltage", "Current"),
        min_family_percent=18.0,
        severity_score_thresholds=(0.11, 0.15),
    ),
    AlertRule(
        name="thermal_overload_temperature",
        root_cause="Thermal overload / overheating trend",
        required_families=("Temperature",),
        min_family_percent=28.0,
        severity_score_thresholds=(0.11, 0.15),
    ),
    AlertRule(
        name="mechanical_wear_vibration_rpm",
        root_cause="Mechanical wear / imbalance",
        required_families=("Vibration", "RPM"),
        min_family_percent=15.0,
        severity_score_thresholds=(0.11, 0.15),
    ),
    AlertRule(
        name="electrical_noise_voltage",
        root_cause="Electrical noise / supply variance",
        required_families=("Voltage",),
        min_family_percent=28.0,
        severity_score_thresholds=(0.11, 0.15),
    ),
]


def _severity_from_score(score: float, warn_thr: float, crit_thr: float) -> str:
    if score >= crit_thr:
        return "CRITICAL"
    if score >= warn_thr:
        return "WARNING"
    return "INFO"


def match_rule(
    families: List[Tuple[str, float]],
    rules: List[AlertRule] = DEFAULT_RULES,
) -> Tuple[Optional[AlertRule], float]:
    fam_map = {k: float(v) for k, v in families}

    best_rule = None
    best_conf = 0.0

    for r in rules:
        ok = True
        conf_parts = []

        for fam in r.required_families:
            pct = fam_map.get(fam, 0.0)
            if pct < r.min_family_percent:
                ok = False
                break
            conf_parts.append(min(1.0, pct / max(1e-6, r.min_family_percent)))

        if not ok:
            continue

        conf = float(np.mean(conf_parts)) if conf_parts else 0.0
        if conf > best_conf:
            best_conf = conf
            best_rule = r

    return best_rule, best_conf


def build_alert_event_from_row(
    *,
    row: pd.Series,
    families: List[Tuple[str, float]],
    top_features: List[Tuple[str, float]],
    score_col: str = "score",
    tag_col: str = "anomaly_tag",
    rules: List[AlertRule] = DEFAULT_RULES,
) -> AlertEvent:
    score = float(row.get(score_col, 0.0))
    ts = str(row.get("timestamp", ""))
    dev = str(row.get("device_id", ""))
    state = str(row.get("state", ""))
    tag = row.get(tag_col, "")
    tag = "" if pd.isna(tag) else str(tag).strip()

    rule, conf = match_rule(families, rules=rules)

    if rule is None:
        top_family = families[0][0] if families else "Other"
        root = f"Anomaly dominated by {top_family}"
        severity = _severity_from_score(score, 0.11, 0.15)
        return AlertEvent(
            timestamp=ts,
            device_id=dev,
            state=state,
            score=score,
            severity=severity,
            root_cause=root,
            confidence=0.35,
            families=families,
            top_features=top_features,
            tag=tag,
            rule_name="fallback_top_family",
        )

    warn_thr, crit_thr = rule.severity_score_thresholds
    severity = _severity_from_score(score, warn_thr, crit_thr)

    return AlertEvent(
        timestamp=ts,
        device_id=dev,
        state=state,
        score=score,
        severity=severity,
        root_cause=rule.root_cause,
        confidence=float(conf),
        families=families,
        top_features=top_features,
        tag=tag,
        rule_name=rule.name,
    )


def print_alerts(alerts: List[AlertEvent], top_n: int = 20) -> None:
    print("\nALERTS (operator-ready):")
    if not alerts:
        print("(no alerts emitted)")
        return

    for a in alerts[:top_n]:
        fam_str = ", ".join([f"{k}={v:.1f}%" for k, v in a.families[:3]])
        print(
            f"- {a.severity} | {a.timestamp} | {a.device_id} | {a.state} | score={a.score:.4f} | "
            f"cause={a.root_cause} | conf={a.confidence:.2f} | {fam_str}"
        )
        for fname, pct in a.top_features[:5]:
            print(f"    {fname}: {pct:.1f}%")
        if a.tag:
            print(f"    tag={a.tag}")
        print(f"    rule={a.rule_name}\n")


def alerts_to_json(alerts: List[AlertEvent]) -> List[dict]:
    return [asdict(a) for a in alerts]
