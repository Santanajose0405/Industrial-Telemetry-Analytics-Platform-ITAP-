"""
Baseline anomaly detection model.

We use IsolationForest because:
- It is a strong unsupervised baseline
- Requires minimal tuning to get useful signals
- Works well for mixed telemetry features

We treat anomaly detection as a scoring problem and evaluate against anomaly_tag.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


@dataclass
class AnomalyPipeline:
    """
    Minimal pipeline: StandardScaler + IsolationForest.

    We keep this explicit (instead of sklearn Pipeline) to make serialization
    and inspection straightforward for portfolio readers.
    """
    scaler: StandardScaler
    model: IsolationForest

    def fit(self, X: pd.DataFrame) -> "AnomalyPipeline":
        Xs = self.scaler.fit_transform(X)
        self.model.fit(Xs)
        return self

    def score(self, X: pd.DataFrame) -> np.ndarray:
        """
        Return anomaly scores where higher means "more anomalous".

        IsolationForest's decision_function is higher for inliers, so we invert it.
        """
        Xs = self.scaler.transform(X)
        inlier_score = self.model.decision_function(Xs)
        return -inlier_score

    def predict(self, X: pd.DataFrame, threshold: float) -> np.ndarray:
        scores = self.score(X)
        return (scores >= threshold).astype(int)


def train_anomaly_model(
    X: pd.DataFrame,
    contamination: float = 0.02,
    random_state: int = 42,
) -> AnomalyPipeline:
    """
    Train an IsolationForest-based anomaly model.

    contamination is an estimate of anomaly prevalence; we treat it as a tuning knob.
    """
    scaler = StandardScaler()
    model = IsolationForest(
        n_estimators=200,
        contamination=float(contamination),
        random_state=int(random_state),
        n_jobs=-1,
    )
    return AnomalyPipeline(scaler=scaler, model=model).fit(X)


def save_pipeline(p: AnomalyPipeline, path: str) -> None:
    joblib.dump(p, path)


def load_pipeline(path: str) -> AnomalyPipeline:
    return joblib.load(path)
