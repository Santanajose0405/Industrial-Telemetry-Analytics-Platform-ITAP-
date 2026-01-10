"""
Baseline anomaly detection model.

We use IsolationForest because:
- It is a strong unsupervised baseline
- Requires minimal tuning to get useful signals
- Works well for mixed telemetry features

We treat anomaly detection as a scoring problem and evaluate against anomaly_tag.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple, List, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


@dataclass
class AnomalyPipeline:
    """
    Minimal pipeline: StandardScaler + IsolationForest.

    Stores feature_names_ at fit-time and enforces column order at score-time.
    """
    scaler: StandardScaler
    model: IsolationForest
    feature_names_: Optional[List[str]] = field(default=None)

    def fit(self, X: pd.DataFrame) -> "AnomalyPipeline":
        self.feature_names_ = list(X.columns)
        Xs = self.scaler.fit_transform(X)
        self.model.fit(Xs)
        return self

    def _align(self, X: pd.DataFrame) -> pd.DataFrame:
        if not self.feature_names_:
            return X
        # Reindex to match training; missing columns become 0.0 (defensive)
        X_aligned = X.reindex(columns=self.feature_names_, fill_value=0.0)
        return X_aligned

    def score(self, X: pd.DataFrame) -> np.ndarray:
        """
        Return anomaly scores where higher means "more anomalous".
        IsolationForest decision_function is higher for inliers, so we invert it.
        """
        X = self._align(X)
        Xs = self.scaler.transform(X)
        inlier_score = self.model.decision_function(Xs)
        return -inlier_score

    def predict(self, X: pd.DataFrame, threshold: float) -> np.ndarray:
        scores = self.score(X)
        return (scores >= threshold).astype(int)


def train_anomaly_model(
    X_train: pd.DataFrame,
    contamination: float = 0.02,
    n_estimators: int = 100,
    random_state: int = 42,
) -> AnomalyPipeline:
    """
    Train an AnomalyPipeline on normal telemetry data.
    
    Args:
        X_train: Feature matrix (should contain mostly normal/non-anomalous data)
        contamination: Expected proportion of outliers in training data
        n_estimators: Number of trees in IsolationForest
        random_state: Random seed for reproducibility
    
    Returns:
        Fitted AnomalyPipeline ready for scoring
    """
    scaler = StandardScaler()
    model = IsolationForest(
        contamination=contamination,
        n_estimators=n_estimators,
        random_state=random_state,
        n_jobs=-1,  # Use all CPU cores
    )
    
    pipeline = AnomalyPipeline(scaler=scaler, model=model)
    pipeline.fit(X_train)
    
    return pipeline  # This MUST be indented as part of the function


def save_pipeline(pipeline: AnomalyPipeline, path: str) -> None:
    """
    Save a trained pipeline to disk using joblib.
    
    Args:
        pipeline: Fitted AnomalyPipeline
        path: File path to save to (e.g., "artifacts/isoforest.joblib")
    """
    joblib.dump(pipeline, path)


def load_pipeline(path: str) -> AnomalyPipeline:
    """
    Load a trained pipeline from disk.
    
    Args:
        path: File path to load from
    
    Returns:
        Loaded AnomalyPipeline ready for scoring
    """
    return joblib.load(path)