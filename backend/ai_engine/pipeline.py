import os
import json
import joblib
import logging
import threading
import numpy as np
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session

from ai_engine.features import extract_all_features, get_bootstrap_labels, extract_features_for_customer
from ai_engine.anomaly import TransactionAnomalyDetector
from ai_engine.classifier import RiskClassifier, RISK_LABELS
from ai_engine.graph_analysis import VendorHubDetector
from models import RiskScore, Customer

logger = logging.getLogger(__name__)

MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'models_store')
os.makedirs(MODEL_DIR, exist_ok=True)

ANOMALY_MODEL_PATH = os.path.join(MODEL_DIR, 'anomaly_detector.joblib')
CLASSIFIER_MODEL_PATH = os.path.join(MODEL_DIR, 'risk_classifier.joblib')
PIPELINE_META_PATH = os.path.join(MODEL_DIR, 'pipeline_meta.json')


class AIPipeline:
    """Main AI pipeline for banking audit risk scoring."""

    def __init__(self):
        self.anomaly_detector = TransactionAnomalyDetector()
        self.classifier = RiskClassifier()
        self.hub_detector = VendorHubDetector()
        self.features_df = None
        self.last_trained = None
        self.last_scored = None
        self.model_metrics = {}
        self._lock = threading.Lock()
        self._load_models()

    def _load_models(self):
        """Load saved models from disk if they exist."""
        if os.path.exists(ANOMALY_MODEL_PATH):
            try:
                self.anomaly_detector = joblib.load(ANOMALY_MODEL_PATH)
                logger.info("Anomaly detector loaded from disk.")
            except Exception as e:
                logger.warning(f"Could not load anomaly model: {e}")

        if os.path.exists(CLASSIFIER_MODEL_PATH):
            try:
                self.classifier = joblib.load(CLASSIFIER_MODEL_PATH)
                logger.info("Risk classifier loaded from disk.")
            except Exception as e:
                logger.warning(f"Could not load classifier model: {e}")

        if os.path.exists(PIPELINE_META_PATH):
            try:
                with open(PIPELINE_META_PATH, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                self.last_trained = meta.get('last_trained')
                self.last_scored = meta.get('last_scored')
                self.model_metrics = meta.get('model_metrics', {})
            except Exception as e:
                logger.warning(f"Could not load pipeline metadata: {e}")

    def _save_models(self):
        """Persist models and metadata to disk."""
        try:
            joblib.dump(self.anomaly_detector, ANOMALY_MODEL_PATH)
            joblib.dump(self.classifier, CLASSIFIER_MODEL_PATH)
            meta = {
                'last_trained': self.last_trained,
                'last_scored': self.last_scored,
                'model_metrics': self.model_metrics
            }
            with open(PIPELINE_META_PATH, 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save models: {e}")

    def train(self, db: Session):
        """Full training pipeline:
        1. Build vendor hub graph
        2. Extract features for all customers
        3. Generate bootstrap labels
        4. Train Isolation Forest (anomaly)
        5. Train Random Forest (classifier)
        6. Save models
        """
        with self._lock:
            logger.info("[AI Pipeline] Starting training...")

            # Step 1: Build vendor hub graph
            logger.info("[AI Pipeline] Building vendor hub graph...")
            try:
                self.hub_detector.build_graph(db)
            except Exception as e:
                logger.warning(f"[AI Pipeline] Hub graph build failed: {e}")

            # Step 2: Extract features
            logger.info("[AI Pipeline] Extracting features...")
            try:
                self.features_df = extract_all_features(db, hub_detector=self.hub_detector)
            except Exception as e:
                logger.error(f"[AI Pipeline] Feature extraction failed: {e}")
                return {}

            if self.features_df.empty:
                logger.warning("[AI Pipeline] No features extracted, skipping training.")
                return {}

            # Step 3: Bootstrap labels
            logger.info("[AI Pipeline] Generating bootstrap labels...")
            labels = get_bootstrap_labels(db)
            labels = labels.reindex(self.features_df.index).fillna(0).astype(int)

            # Ensure at least 2 classes for training
            unique_labels = labels.unique()
            if len(unique_labels) < 2:
                # Add synthetic diversity if all labels are the same
                logger.warning("[AI Pipeline] Only one class found in labels — adding synthetic labels.")
                n = len(labels)
                labels.iloc[: max(1, n // 10)] = 1  # Mark ~10% as Amber
                labels.iloc[: max(1, n // 20)] = 2  # Mark ~5% as Red

            # Step 4: Train anomaly detector
            logger.info("[AI Pipeline] Training Isolation Forest...")
            try:
                self.anomaly_detector.fit(self.features_df)
            except Exception as e:
                logger.error(f"[AI Pipeline] Anomaly detector training failed: {e}")

            # Step 5: Compute anomaly scores and add as feature
            anomaly_scores = np.zeros(len(self.features_df))
            if self.anomaly_detector.is_fitted:
                try:
                    anomaly_scores = self.anomaly_detector.score(self.features_df)
                except Exception as e:
                    logger.warning(f"[AI Pipeline] Could not compute anomaly scores: {e}")

            features_with_anomaly = self.features_df.copy()
            features_with_anomaly['anomaly_score'] = anomaly_scores

            # Step 6: Train classifier
            logger.info("[AI Pipeline] Training Random Forest classifier...")
            try:
                self.classifier.fit(features_with_anomaly, labels)
            except Exception as e:
                logger.error(f"[AI Pipeline] Classifier training failed: {e}")
                return {}

            # Collect metrics
            self.last_trained = datetime.now().isoformat()
            label_counts = labels.value_counts().to_dict()
            cv_mean = float(np.mean(self.classifier.cv_scores)) if self.classifier.cv_scores else 0.0

            self.model_metrics = {
                'n_samples': len(self.features_df),
                'n_features': len(features_with_anomaly.columns),
                'label_distribution': {
                    RISK_LABELS.get(k, str(k)): int(v) for k, v in label_counts.items()
                },
                'cv_f1_mean': round(cv_mean, 4),
                'cv_f1_scores': [round(s, 4) for s in self.classifier.cv_scores],
                'top_features': sorted(
                    [
                        (k, round(v, 4))
                        for k, v in (self.classifier.feature_importances_ or {}).items()
                    ],
                    key=lambda x: x[1], reverse=True
                )[:10],
                'anomaly_contamination': 0.15,
                'n_estimators_rf': 200,
                'n_estimators_if': 100,
            }

            self._save_models()
            logger.info(f"[AI Pipeline] Training complete. CV F1={cv_mean:.4f}")
            return self.model_metrics

    def score_all(self, db: Session):
        """Score all customers and update RiskScore table in DB."""
        logger.info("[AI Pipeline] Running batch scoring...")

        if not self.classifier.is_fitted:
            logger.warning("[AI Pipeline] Classifier not fitted. Running training first...")
            self.train(db)

        # Rebuild hub graph for latest data
        try:
            self.hub_detector.build_graph(db)
        except Exception as e:
            logger.warning(f"[AI Pipeline] Hub rebuild failed: {e}")

        try:
            self.features_df = extract_all_features(db, hub_detector=self.hub_detector)
        except Exception as e:
            logger.error(f"[AI Pipeline] Feature extraction failed during scoring: {e}")
            return 0

        if self.features_df.empty:
            logger.warning("[AI Pipeline] No features to score.")
            return 0

        # Compute anomaly scores
        anomaly_scores = np.zeros(len(self.features_df))
        if self.anomaly_detector.is_fitted:
            try:
                anomaly_scores = self.anomaly_detector.score(self.features_df)
            except Exception as e:
                logger.warning(f"[AI Pipeline] Anomaly scoring failed: {e}")

        features_with_anomaly = self.features_df.copy()
        features_with_anomaly['anomaly_score'] = anomaly_scores

        # Get model predictions
        try:
            probas = self.classifier.predict_proba(features_with_anomaly)
            predictions = np.argmax(probas, axis=1)
        except Exception as e:
            logger.error(f"[AI Pipeline] Prediction failed: {e}")
            return 0

        today = datetime.now().strftime("%Y-%m-%d")
        updated_count = 0

        for i, (cif, row) in enumerate(self.features_df.iterrows()):
            try:
                pred_label = int(predictions[i])
                risk_category = RISK_LABELS[pred_label]

                # Composite risk score (0-100)
                p_amber = float(probas[i][1])
                p_red = float(probas[i][2])
                anomaly_s = float(anomaly_scores[i])
                risk_score = int(min(100, (p_amber * 40 + p_red * 80 + anomaly_s * 0.2)))

                # Generate explanations
                feature_dict = {
                    k: float(features_with_anomaly.loc[cif, k])
                    for k in features_with_anomaly.columns
                    if k in features_with_anomaly.columns
                }
                explanations = self.classifier.explain(feature_dict, top_n=6)

                # Prepend anomaly explanation if anomaly score is high
                if anomaly_s > 60:
                    explanations.insert(0, {
                        'rule_id': 'AI_ANOMALY',
                        'description': (
                            f"Mô hình phát hiện bất thường giao dịch (điểm: {anomaly_s:.0f}/100)"
                        ),
                        'feature': 'anomaly_score',
                        'value': round(anomaly_s, 1),
                        'importance_pct': round(anomaly_s / 100 * 25, 1),
                        'severity': 'high' if anomaly_s > 80 else 'medium',
                        'points': int(anomaly_s * 0.25)
                    })

                rule_hits_json = json.dumps(explanations, ensure_ascii=False)

                # Upsert into DB
                existing = db.query(RiskScore).filter(RiskScore.cif == cif).first()
                if existing:
                    existing.total_score = risk_score
                    existing.risk_category = risk_category
                    existing.rule_hits = rule_hits_json
                    existing.score_date = today
                    existing.last_updated = today
                else:
                    db.add(RiskScore(
                        cif=cif,
                        score_date=today,
                        total_score=risk_score,
                        risk_category=risk_category,
                        rule_hits=rule_hits_json,
                        last_updated=today
                    ))
                updated_count += 1

            except Exception as e:
                logger.warning(f"[AI Pipeline] Failed to score CIF={cif}: {e}")
                continue

        try:
            db.commit()
        except Exception as e:
            logger.error(f"[AI Pipeline] DB commit failed: {e}")
            db.rollback()

        self.last_scored = datetime.now().isoformat()
        self._save_models()

        logger.info(f"[AI Pipeline] Scored {updated_count} customers.")
        return updated_count

    def score_single(self, cif: str, db: Session) -> dict:
        """Score a single customer on demand."""
        if not self.classifier.is_fitted:
            self.train(db)

        hub_feats = self.hub_detector.get_hub_features(cif)
        try:
            features = extract_features_for_customer(cif, db, hub_features=hub_feats)
        except Exception as e:
            logger.error(f"[AI Pipeline] Feature extraction failed for {cif}: {e}")
            return {}

        if not features:
            return {}

        df = pd.DataFrame([features])

        # Ensure all expected columns are present
        for col in (self.classifier.feature_names or []):
            if col not in df.columns:
                df[col] = 0

        # Anomaly score
        anomaly_s = 0.0
        if self.anomaly_detector.is_fitted:
            try:
                anomaly_s = self.anomaly_detector.score_single(features)
            except Exception:
                pass

        df['anomaly_score'] = anomaly_s

        try:
            proba = self.classifier.predict_proba(df)[0]
        except Exception as e:
            logger.error(f"[AI Pipeline] Predict failed for {cif}: {e}")
            return {}

        pred = int(np.argmax(proba))
        risk_category = RISK_LABELS[pred]
        risk_score = int(min(100, (proba[1] * 40 + proba[2] * 80 + anomaly_s * 0.2)))

        feature_dict = {col: float(df[col].values[0]) for col in df.columns}
        explanations = self.classifier.explain(feature_dict, top_n=6)

        return {
            'risk_score': risk_score,
            'risk_category': risk_category,
            'probabilities': {
                'Green': round(float(proba[0]), 4),
                'Amber': round(float(proba[1]), 4),
                'Red': round(float(proba[2]), 4),
            },
            'anomaly_score': round(anomaly_s, 1),
            'rule_hits': explanations,
            'model_version': self.last_trained or 'unknown',
        }

    def get_model_info(self) -> dict:
        """Return model metadata and current status."""
        return {
            'last_trained': self.last_trained,
            'last_scored': self.last_scored,
            'classifier_fitted': self.classifier.is_fitted,
            'anomaly_fitted': self.anomaly_detector.is_fitted,
            'metrics': self.model_metrics,
            'models': {
                'risk_classifier': {
                    'type': 'RandomForestClassifier',
                    'n_estimators': 200,
                    'max_depth': 8,
                    'classes': ['Green', 'Amber', 'Red'],
                    'cv_f1_mean': self.model_metrics.get('cv_f1_mean', 0)
                },
                'anomaly_detector': {
                    'type': 'IsolationForest',
                    'n_estimators': 100,
                    'contamination': 0.15,
                    'features': self.anomaly_detector.feature_names
                },
                'vendor_hub_detector': {
                    'type': 'NetworkX Graph Analysis',
                    'algorithm': 'Bipartite Graph - Hub Detection (degree >= 3)',
                    'hub_vendors_found': len(self.hub_detector.hub_vendors)
                }
            },
            'feature_names': self.classifier.feature_names or [],
            'top_features': self.model_metrics.get('top_features', [])
        }


# Global singleton with thread safety
_pipeline_instance = None
_pipeline_lock = threading.Lock()


def get_pipeline() -> AIPipeline:
    global _pipeline_instance
    if _pipeline_instance is None:
        with _pipeline_lock:
            if _pipeline_instance is None:
                _pipeline_instance = AIPipeline()
    return _pipeline_instance
