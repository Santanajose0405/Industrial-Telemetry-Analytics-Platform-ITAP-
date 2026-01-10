"""
Evaluation utilities for anomaly scoring.

We compute standard classification metrics by turning scores into binary predictions
using a chosen threshold. This makes results interpretable and comparable.
"""

from __future__ import annotations

from typing import Dict

import numpy as np
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score


def evaluate_scores(y_true: np.ndarray, scores: np.ndarray, threshold: float) -> Dict[str, float]:
    y_pred = (scores >= float(threshold)).astype(int)

    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="binary", zero_division=0
    )

    # ROC-AUC is meaningful only if both classes exist.
    auc = None
    if len(set(y_true.tolist())) == 2:
        auc = roc_auc_score(y_true, scores)

    return {
        "threshold": float(threshold),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "roc_auc": float(auc) if auc is not None else float("nan"),
    }
