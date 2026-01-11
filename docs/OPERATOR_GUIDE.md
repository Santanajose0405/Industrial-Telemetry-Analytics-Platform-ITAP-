# ITAP Operator Guide
**Industrial Telemetry Analytics Platform**

## Purpose
ITAP detects abnormal industrial telemetry patterns and converts raw anomaly scores
into **actionable, operator-ready alerts** with clear routing, confidence, and root cause context.

This guide explains:
- What alerts mean
- How alerts are generated
- How operators should respond

---

## Alert Lifecycle (High-Level)

1. Telemetry is ingested and scored by the anomaly model
2. Anomalies are explained using feature attribution
3. Alerts are generated using rule-based logic
4. Alerts are routed to the appropriate operational team
5. Aggregates support prioritization and planning

---

## Alert Types

### 1. Burst Alerts
**Rule:** N anomalies within M minutes per device

**What it means**
- Rapid anomaly clustering
- Often indicates unstable operation or cascading failures

**Example**
> 3 anomalies within 10 minutes on DEV-001

**Recommended Action**
- Inspect device health immediately
- Check recent configuration or load changes

---

### 2. Dominant Sensor Family Alerts
**Rule:** A single sensor family exceeds a contribution threshold (e.g., 45%)

**Examples**
- Voltage dominance → electrical instability
- Temperature dominance → overheating or cooling failure
- Vibration + RPM → mechanical wear

**Recommended Action**
- Focus troubleshooting on the dominant subsystem
- Review recent trends for that sensor family

---

### 3. Tagged Fault Routing Alerts
**Rule:** Known anomaly tags route alerts to owners

| Tag | Route |
|----|------|
| `bearing_wear` | Maintenance |
| `overheat_drift` | Thermal |
| `power_spike` | Electrical |

**Recommended Action**
- Follow your team’s standard operating procedure
- Escalate if repeated alerts occur

---

## Alert Fields Explained

| Field | Description |
|-----|------------|
| severity | INFO / WARNING / CRITICAL |
| confidence | Likelihood the alert represents a real issue |
| rule_id | Rule that generated the alert |
| root_cause | Human-readable explanation |
| families | Sensor-family contribution breakdown |
| top_features | Highest contributing telemetry features |

---

## Alert Confidence
Confidence is calculated based on:
- Degree of dominance over thresholds
- Rule specificity
- Signal consistency

Higher confidence = higher priority.

---

## Aggregated Views

ITAP produces fleet and device-level summaries:

- Total anomaly count
- Average severity
- p95 severity
- Dominant sensor families

**Use aggregates to:**
- Identify problematic devices
- Plan preventive maintenance
- Track long-term degradation

---

## Operational Best Practices

- Treat **burst alerts** as time-sensitive
- Use **dominant-family alerts** for targeted diagnostics
- Use **aggregates** for planning, not firefighting
- Repeated alerts on the same device warrant escalation

---

## Known Limitations
- Alerts depend on telemetry quality
- Rule thresholds should be tuned per environment
- Model retraining cadence affects sensitivity

---

## Support
This system is designed to be:
- Explainable
- Auditable
- Configurable

Contact your platform or data engineering team for rule updates.
