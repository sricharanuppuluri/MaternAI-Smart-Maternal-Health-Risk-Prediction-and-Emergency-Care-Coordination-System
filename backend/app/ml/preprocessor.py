"""Feature preprocessing and alignment transformer for MaternAI ML pipeline.

This module provides a reproducible scikit-learn compatible transformer that ensures
input data contains all expected physiological features with safe median fallbacks.
"""

from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

FEATURE_COLS: List[str] = [
    "Age",
    "SystolicBP",
    "DiastolicBP",
    "BS",
    "BodyTemp",
    "HeartRate",
]

DEFAULT_MEDIANS: Dict[str, float] = {
    "Age": 25.0,
    "SystolicBP": 120.0,
    "DiastolicBP": 80.0,
    "BS": 7.5,
    "BodyTemp": 98.0,
    "HeartRate": 76.0,
}


class FeatureImputerAndAligner(BaseEstimator, TransformerMixin):
    """Transformer ensuring deterministic feature ordering and median imputation for null vitals."""

    def __init__(self, feature_names: Optional[List[str]] = None):
        self.feature_names = feature_names or list(FEATURE_COLS)
        self.medians_: Dict[str, float] = {}

    def fit(self, X, y=None):
        df_x = pd.DataFrame(X, columns=self.feature_names) if not isinstance(X, pd.DataFrame) else X
        for col in self.feature_names:
            if col in df_x.columns and not df_x[col].dropna().empty:
                self.medians_[col] = float(df_x[col].median())
            else:
                self.medians_[col] = DEFAULT_MEDIANS.get(col, 0.0)
        return self

    def transform(self, X):
        df_x = pd.DataFrame(X, columns=self.feature_names).copy() if not isinstance(X, pd.DataFrame) else X.copy()
        for col in self.feature_names:
            fallback = float(self.medians_.get(col, DEFAULT_MEDIANS.get(col, 0.0)))
            if col not in df_x.columns:
                df_x[col] = fallback
            else:
                df_x[col] = pd.to_numeric(df_x[col], errors="coerce").fillna(fallback)
        return df_x[self.feature_names].to_numpy(dtype=float)
