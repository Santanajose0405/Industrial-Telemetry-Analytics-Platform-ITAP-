from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score


def threshold_sweep(
    y_true: np.ndarray,
    scores: np.ndarray,
    thresholds: Optional[List[float]] = None,
) -> Tuple[List[Dict[str, float]], Dict[str, float]]:
    """
    Sweep thresholds and report metrics sorted by recall then precision.

    Conventions:
      - y_true: 1 = anomalous, 0 = normal
      - scores: higher = more anomalous
      - prediction rule: pred = (scores >= threshold)

    Returns:
      (results_list, selected_best)
    """
    y_true = np.asarray(y_true, dtype=int)
    scores = np.asarray(scores, dtype=float)

    if y_true.shape[0] != scores.shape[0]:
        raise ValueError(f"y_true length {len(y_true)} does not match scores length {len(scores)}")

    # If caller doesn't provide thresholds, generate a stable set from quantiles.
    if thresholds is None:
        quantiles = [0.90, 0.92, 0.94, 0.96, 0.98]
        thresholds = sorted(set(float(np.quantile(scores, q)) for q in quantiles))

    # roc_auc expects higher score => more likely positive
    try:
        auc = float(roc_auc_score(y_true, scores))
    except Exception:
        auc = 0.0

    results: List[Dict[str, float]] = []
    for thr in thresholds:
        y_pred = (scores >= float(thr)).astype(int)

        p = float(precision_score(y_true, y_pred, zero_division=0))
        r = float(recall_score(y_true, y_pred, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, zero_division=0))

        results.append(
            {
                "threshold": float(thr),
                "precision": p,
                "recall": r,
                "f1": f1,
                "roc_auc": auc,
            }
        )

    # Operator-friendly selection: prefer recall first, then precision.
    results.sort(key=lambda d: (d["recall"], d["precision"]), reverse=True)
    selected = results[0] if results else {"threshold": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0, "roc_auc": auc}

    return results, selected


def per_tag_recall(
    df_scored: pd.DataFrame,
    *,
    pred_col: str = "pred",
    tag_col: str = "anomaly_tag",
) -> List[Dict[str, object]]:
    """
    Compute recall per anomaly tag on tagged rows only.

    This is particularly useful in your synthetic dataset because anomaly_tag is your injected ground truth.
    We treat any non-empty anomaly_tag as "true anomaly" and compute recall per tag.
    """
    if df_scored is None or df_scored.empty:
        return []

    if tag_col not in df_scored.columns or pred_col not in df_scored.columns:
        return []

    tags = df_scored[tag_col].fillna("").astype(str).str.strip()
    tagged = df_scored[tags != ""].copy()
    if tagged.empty:
        return []

    out: List[Dict[str, object]] = []
    for tag, g in tagged.groupby(tag_col):
        y_pred = g[pred_col].astype(int).to_numpy()
        tp = int((y_pred == 1).sum())
        fn = int((y_pred == 0).sum())

        recall = float(tp / max(1, tp + fn))
        out.append({"tag": str(tag), "recall": recall, "tp": tp, "fn": fn})

    out.sort(key=lambda d: d["recall"], reverse=True)
    return out
