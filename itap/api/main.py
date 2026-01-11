"""
ITAP FastAPI service (artifact-backed, read-only).

Purpose
-------
Expose ITAP scoring outputs (alerts, aggregates, metrics) via a typed REST API.
This is the fastest "operator-ready" web layer because it reads the JSON artifacts
produced by `python -m itap.ml.run_score`.

Endpoints
---------
- GET  /api/health
- GET  /api/metrics
- GET  /api/alerts
- GET  /api/alerts/{alert_id}
- GET  /api/aggregates
- GET  /api/aggregates/{device_id}

Design notes
------------
- Read-only by default (safe and simple for portfolio + demos).
- Artifact-backed (no DB required). Later you can evolve to DB-backed storage.
- Pydantic models provide a stable contract and OpenAPI docs.

How to run (dev)
----------------
pip install fastapi uvicorn
uvicorn itap.api.main:app --reload

Then open:
- http://127.0.0.1:8000/docs
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict


# -----------------------------
# Configuration
# -----------------------------

# Default location of artifacts produced by `itap.ml.run_score`.
DEFAULT_ARTIFACT_DIR = Path("artifacts")

# Common artifact file names (adjust if your project uses different names).
ALERTS_FILE = "alerts.json"
AGGREGATES_FILE = "aggregate_summaries.json"
METRICS_FILE = "metrics.json"

# Optional explainability artifact (if you persist one).
EXPLANATIONS_FILE = "explanations_top.json"


# -----------------------------
# Pydantic models (API contract)
# -----------------------------

class HealthResponse(BaseModel):
    status: str = "ok"
    artifact_dir: str
    artifacts_present: Dict[str, bool]
    artifacts_mtime_utc: Dict[str, Optional[str]]


class MetricsResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    # metrics.json contents can vary; we allow extra keys.
    # Typical keys: threshold, precision, recall, f1, roc_auc
    threshold: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1: Optional[float] = None
    roc_auc: Optional[float] = None


class AlertEvent(BaseModel):
    """
    Represents one operator-facing alert. The exact fields depend on your alert engine.
    We keep a flexible contract to avoid breaking when you enhance alerting.

    Recommended fields (if present in alerts.json):
      - id (or alert_id)
      - timestamp
      - device_id
      - severity
      - route
      - cause
      - rule_id
      - score
      - families (dict or list)
      - top_features (list)
    """
    model_config = ConfigDict(extra="allow")

    # Preferred canonical fields
    alert_id: str = Field(..., description="Stable alert identifier (string).")
    timestamp: Optional[str] = Field(None, description="Event timestamp (ISO string).")
    device_id: Optional[str] = Field(None, description="Device identifier.")
    severity: Optional[str] = Field(None, description="Severity label (info/warning/critical).")
    route: Optional[str] = Field(None, description="Operational routing/team (maintenance/thermal/etc).")
    cause: Optional[str] = Field(None, description="Human-readable cause string.")
    rule_id: Optional[str] = Field(None, description="Rule identifier that generated this alert.")
    score: Optional[float] = Field(None, description="Underlying anomaly score or severity score.")


class AggregateSummary(BaseModel):
    """
    Represents a per-device (or fleet) aggregation summary output.
    Your aggregate_summaries.json may be a dict keyed by device_id or a list.
    """
    model_config = ConfigDict(extra="allow")

    device_id: str


# -----------------------------
# Helpers
# -----------------------------

def _iso_utc_from_mtime(path: Path) -> Optional[str]:
    try:
        ts = path.stat().st_mtime
    except FileNotFoundError:
        return None
    return datetime.utcfromtimestamp(ts).replace(microsecond=0).isoformat() + "Z"


def _read_json_file(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(str(path))
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _coerce_alert_id(alert: Dict[str, Any], index_fallback: int) -> str:
    """
    Normalize alerts into a stable 'alert_id' field for API use.

    Priority:
      1) alert_id
      2) id
      3) rule_id + timestamp + device_id (if available)
      4) fallback index-based id (stable per file ordering)
    """
    if isinstance(alert.get("alert_id"), str) and alert["alert_id"].strip():
        return alert["alert_id"].strip()
    if isinstance(alert.get("id"), str) and alert["id"].strip():
        return alert["id"].strip()

    rule_id = str(alert.get("rule_id", "")).strip()
    ts = str(alert.get("timestamp", "")).strip()
    dev = str(alert.get("device_id", "")).strip()

    if rule_id and ts and dev:
        return f"{rule_id}:{dev}:{ts}"

    # Last resort: stable within the file order
    return f"idx:{index_fallback}"


def _normalize_alerts(raw: Any) -> List[Dict[str, Any]]:
    """
    Accepts alerts.json as either:
      - list[dict]
      - dict with 'alerts' key
    Returns a list[dict].
    """
    if raw is None:
        return []
    if isinstance(raw, list):
        return [a for a in raw if isinstance(a, dict)]
    if isinstance(raw, dict):
        if isinstance(raw.get("alerts"), list):
            return [a for a in raw["alerts"] if isinstance(a, dict)]
    return []


def _normalize_aggregates(raw: Any) -> Dict[str, Dict[str, Any]]:
    """
    Accepts aggregate_summaries.json as either:
      - dict keyed by device_id -> summary dict
      - list of summary dicts containing device_id
    Returns dict keyed by device_id.
    """
    if raw is None:
        return {}

    if isinstance(raw, dict):
        # Assume already keyed by device_id
        out: Dict[str, Dict[str, Any]] = {}
        for k, v in raw.items():
            if isinstance(v, dict):
                v2 = dict(v)
                v2.setdefault("device_id", str(k))
                out[str(k)] = v2
        return out

    if isinstance(raw, list):
        out = {}
        for item in raw:
            if not isinstance(item, dict):
                continue
            dev = item.get("device_id")
            if dev is None:
                continue
            out[str(dev)] = item
        return out

    return {}


def _try_parse_iso(ts: Optional[str]) -> Optional[datetime]:
    if ts is None:
        return None
    s = str(ts).strip()
    if not s:
        return None
    # Be tolerant: remove trailing Z then interpret as naive UTC if present
    if s.endswith("Z"):
        s = s[:-1]
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


# -----------------------------
# FastAPI app
# -----------------------------

app = FastAPI(
    title="ITAP API",
    version="0.1.0",
    description="Artifact-backed API for ITAP (Industrial Telemetry Analytics Platform).",
)

# For React dev (Vite) you typically want CORS enabled.
# In production, restrict origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later (e.g., ["http://localhost:5173"])
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Dependency-like accessors
# -----------------------------

@dataclass(frozen=True)
class ArtifactPaths:
    artifact_dir: Path
    alerts_path: Path
    aggregates_path: Path
    metrics_path: Path
    explanations_path: Path


def get_paths(artifact_dir: Optional[str] = None) -> ArtifactPaths:
    base = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return ArtifactPaths(
        artifact_dir=base,
        alerts_path=base / ALERTS_FILE,
        aggregates_path=base / AGGREGATES_FILE,
        metrics_path=base / METRICS_FILE,
        explanations_path=base / EXPLANATIONS_FILE,
    )


# -----------------------------
# Routes
# -----------------------------

@app.get("/api/health", response_model=HealthResponse)
def health(artifact_dir: Optional[str] = Query(None, description="Override artifact directory path")) -> HealthResponse:
    paths = get_paths(artifact_dir)

    artifacts = {
        "metrics.json": paths.metrics_path.exists(),
        "alerts.json": paths.alerts_path.exists(),
        "aggregate_summaries.json": paths.aggregates_path.exists(),
        "explanations_top.json": paths.explanations_path.exists(),
    }

    mtimes = {
        "metrics.json": _iso_utc_from_mtime(paths.metrics_path),
        "alerts.json": _iso_utc_from_mtime(paths.alerts_path),
        "aggregate_summaries.json": _iso_utc_from_mtime(paths.aggregates_path),
        "explanations_top.json": _iso_utc_from_mtime(paths.explanations_path),
    }

    return HealthResponse(
        status="ok",
        artifact_dir=str(paths.artifact_dir.resolve()),
        artifacts_present=artifacts,
        artifacts_mtime_utc=mtimes,
    )


@app.get("/api/metrics", response_model=MetricsResponse)
def metrics(artifact_dir: Optional[str] = Query(None, description="Override artifact directory path")) -> MetricsResponse:
    paths = get_paths(artifact_dir)
    try:
        raw = _read_json_file(paths.metrics_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Missing artifact: {paths.metrics_path}")

    if not isinstance(raw, dict):
        raise HTTPException(status_code=500, detail="metrics.json must be a JSON object")

    # Let Pydantic accept extras; common fields are included explicitly
    return MetricsResponse(**raw)


@app.get("/api/alerts", response_model=List[AlertEvent])
def list_alerts(
    artifact_dir: Optional[str] = Query(None, description="Override artifact directory path"),
    device_id: Optional[str] = Query(None, description="Filter alerts by device_id"),
    severity: Optional[str] = Query(None, description="Filter alerts by severity (e.g., warning, critical)"),
    route: Optional[str] = Query(None, description="Filter alerts by route/team (e.g., maintenance, thermal)"),
    since: Optional[str] = Query(None, description="Filter alerts with timestamp >= since (ISO string)"),
    limit: int = Query(200, ge=1, le=2000, description="Max number of alerts to return"),
) -> List[AlertEvent]:
    paths = get_paths(artifact_dir)
    try:
        raw = _read_json_file(paths.alerts_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Missing artifact: {paths.alerts_path}")

    alerts = _normalize_alerts(raw)

    since_dt = _try_parse_iso(since)

    filtered: List[Dict[str, Any]] = []
    for i, a in enumerate(alerts):
        a2 = dict(a)

        # Normalize id field for API consumers
        a2["alert_id"] = _coerce_alert_id(a2, i)

        if device_id and str(a2.get("device_id", "")).strip() != device_id:
            continue
        if severity and str(a2.get("severity", "")).strip().lower() != severity.strip().lower():
            continue
        if route and str(a2.get("route", "")).strip().lower() != route.strip().lower():
            continue

        if since_dt is not None:
            ts_dt = _try_parse_iso(a2.get("timestamp"))
            if ts_dt is None:
                # If timestamp is missing/unparseable, skip for a time-bounded query
                continue
            if ts_dt < since_dt:
                continue

        filtered.append(a2)

    # Sort newest-first if timestamps exist
    def _sort_key(x: Dict[str, Any]) -> float:
        dt = _try_parse_iso(x.get("timestamp"))
        return dt.timestamp() if dt else 0.0

    filtered.sort(key=_sort_key, reverse=True)

    return [AlertEvent(**a) for a in filtered[:limit]]


@app.get("/api/alerts/{alert_id}", response_model=AlertEvent)
def get_alert(
    alert_id: str,
    artifact_dir: Optional[str] = Query(None, description="Override artifact directory path"),
) -> AlertEvent:
    paths = get_paths(artifact_dir)
    try:
        raw = _read_json_file(paths.alerts_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Missing artifact: {paths.alerts_path}")

    alerts = _normalize_alerts(raw)

    for i, a in enumerate(alerts):
        if not isinstance(a, dict):
            continue
        a2 = dict(a)
        a2["alert_id"] = _coerce_alert_id(a2, i)
        if a2["alert_id"] == alert_id:
            return AlertEvent(**a2)

    raise HTTPException(status_code=404, detail=f"Alert not found: {alert_id}")


@app.get("/api/aggregates", response_model=List[AggregateSummary])
def list_aggregates(
    artifact_dir: Optional[str] = Query(None, description="Override artifact directory path"),
    limit: int = Query(500, ge=1, le=5000, description="Max number of device summaries to return"),
    sort_by: str = Query("device_id", description="Sort key if present (e.g., device_id, avg_score, p95_score, n)"),
    desc: bool = Query(False, description="Sort descending"),
) -> List[AggregateSummary]:
    paths = get_paths(artifact_dir)
    try:
        raw = _read_json_file(paths.aggregates_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Missing artifact: {paths.aggregates_path}")

    agg_map = _normalize_aggregates(raw)
    summaries = list(agg_map.values())

    # Safe sorting if key exists
    def _safe_sort_key(x: Dict[str, Any]) -> Any:
        v = x.get(sort_by)
        # Prefer numeric sorts when possible
        if isinstance(v, (int, float)):
            return v
        if v is None:
            return "" if sort_by == "device_id" else -1
        return v

    summaries.sort(key=_safe_sort_key, reverse=bool(desc))

    out: List[AggregateSummary] = []
    for s in summaries[:limit]:
        dev = s.get("device_id")
        if dev is None:
            continue
        out.append(AggregateSummary(device_id=str(dev), **s))
    return out


@app.get("/api/aggregates/{device_id}", response_model=AggregateSummary)
def get_aggregate(
    device_id: str,
    artifact_dir: Optional[str] = Query(None, description="Override artifact directory path"),
) -> AggregateSummary:
    paths = get_paths(artifact_dir)
    try:
        raw = _read_json_file(paths.aggregates_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Missing artifact: {paths.aggregates_path}")

    agg_map = _normalize_aggregates(raw)
    if device_id not in agg_map:
        raise HTTPException(status_code=404, detail=f"No aggregate summary found for device_id={device_id}")

    summary = agg_map[device_id]
    return AggregateSummary(device_id=str(device_id), **summary)
