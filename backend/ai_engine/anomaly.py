from sklearn.ensemble import IsolationForest
import numpy as np
import pandas as pd

ANOMALY_FEATURES = [
    'cash_withdrawal_ratio', 'time_to_withdrawal_h', 'round_txn_ratio',
    'txn_velocity', 'avg_ltv', 'si_employee_ratio'
]


class TransactionAnomalyDetector:
    """Isolation Forest-based anomaly detector for transaction patterns."""

    def __init__(self):
        self.model = IsolationForest(
            n_estimators=100, contamination=0.15, random_state=42
        )
        self.is_fitted = False
        self.feature_names = ANOMALY_FEATURES

    def fit(self, X: pd.DataFrame):
        """Train on features DataFrame. Uses ANOMALY_FEATURES columns."""
        # Only use columns that exist in the input DataFrame
        available_features = [f for f in self.feature_names if f in X.columns]
        if not available_features:
            return self
        X_sub = X[available_features].fillna(0)
        self.model.fit(X_sub)
        self.is_fitted = True
        # Update feature_names to only use available ones
        self.feature_names = available_features
        return self

    def score(self, X: pd.DataFrame) -> np.ndarray:
        """Returns anomaly scores 0-100 (higher = more anomalous).
        IsolationForest returns negative scores for anomalies, so we convert."""
        available_features = [f for f in self.feature_names if f in X.columns]
        if not available_features:
            return np.zeros(len(X))
        X_sub = X[available_features].fillna(0)
        raw = self.model.score_samples(X_sub)  # more negative = more anomalous
        # Normalize to 0-100 where 100 = most anomalous
        min_s, max_s = raw.min(), raw.max()
        if max_s == min_s:
            return np.zeros(len(raw))
        normalized = (max_s - raw) / (max_s - min_s) * 100
        return np.clip(normalized, 0, 100)

    def score_single(self, features: dict) -> float:
        """Score a single customer. Returns 0-100."""
        if not self.is_fitted:
            return 0.0
        df = pd.DataFrame([features])
        scores = self.score(df)
        return float(scores[0])
