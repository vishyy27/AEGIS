import os
import joblib
import glob
import json
import hashlib
import threading
import logging
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List
from sqlalchemy.orm import Session
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from ..models.deployment import Deployment

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "ml", "models")
os.makedirs(MODELS_DIR, exist_ok=True)

FEATURE_NAMES = [
    "commit_count", "files_changed", "code_churn", "test_coverage", 
    "dependency_updates", "historical_failures", "deployment_frequency", 
    "churn_ratio", "commit_density", "failure_rate_last_10", 
    "avg_risk_last_5", "has_db_migration", "has_auth_changes", 
    "has_payment_changes", "has_core_module_changes"
]

logger = logging.getLogger("aegis.ml")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(ch)

class MLEngine:
    def __init__(self):
        self.model: Optional[Pipeline] = None
        self.current_version: Optional[str] = None
        self.current_metadata: Dict[str, Any] = {}
        self._train_lock = threading.Lock()
        self.load_model()
        
    def load_model(self) -> bool:
        """Loads the most recent trained model pipeline from disk and its metadata."""
        model_files = glob.glob(os.path.join(MODELS_DIR, "risk_model_*.pkl"))
        if not model_files:
            self.model = None
            self.current_version = None
            self.current_metadata = {}
            return False
            
        model_files.sort(reverse=True)
        latest_model = model_files[0]
        meta_filepath = latest_model.replace(".pkl", ".meta.json")
        
        try:
            self.model = joblib.load(latest_model)
            self.current_version = os.path.basename(latest_model)
            
            if os.path.exists(meta_filepath):
                with open(meta_filepath, "r") as f:
                    self.current_metadata = json.load(f)
                logger.info(f"[ML] version={self.current_version} meta_loaded=True samples={self.current_metadata.get('samples_trained')} created={self.current_metadata.get('created_at')}")
            else:
                self.current_metadata = {}
                logger.warning(f"[ML] version={self.current_version} meta_loaded=False")
                
            return True
        except Exception as e:
            logger.error(f"[ML] load_failed={latest_model} error={str(e)}")
            self.model = None
            self.current_version = None
            self.current_metadata = {}
            return False
            
    def prepare_features(self, deployment: Deployment) -> List[float]:
        """Extracts and formats features for the ML model with Data Validation."""
        sensitive_files = []
        if deployment.sensitive_files:
            try:
                if isinstance(deployment.sensitive_files, str):
                    sensitive_files = json.loads(deployment.sensitive_files)
                elif isinstance(deployment.sensitive_files, list):
                    sensitive_files = deployment.sensitive_files
            except json.JSONDecodeError:
                pass
                
        has_db_migration = deployment.has_db_migration or any("db" in f.lower() for f in sensitive_files)
        has_auth_changes = deployment.has_auth_changes or any("auth" in f.lower() for f in sensitive_files)
        has_payment_changes = deployment.has_payment_changes or any("payment" in f.lower() for f in sensitive_files)
        has_core_module_changes = deployment.has_core_module_changes or any("config" in f.lower() for f in sensitive_files)
        
        deployment.has_db_migration = has_db_migration
        deployment.has_auth_changes = has_auth_changes
        deployment.has_payment_changes = has_payment_changes
        deployment.has_core_module_changes = has_core_module_changes

        # Phase 8.3 Data Validation bounds
        test_coverage = float(deployment.test_coverage if deployment.test_coverage is not None else 100.0)
        test_coverage = min(max(test_coverage, 0.0), 100.0)

        # Build feature vector
        features = [
            float(deployment.commit_count if deployment.commit_count is not None else 0.0),
            float(deployment.files_changed if deployment.files_changed is not None else 0.0),
            float(deployment.code_churn if deployment.code_churn is not None else 0.0),
            test_coverage,
            float(deployment.dependency_updates if deployment.dependency_updates is not None else 0.0),
            float(deployment.historical_failures if deployment.historical_failures is not None else 0.0),
            float(deployment.deployment_frequency if deployment.deployment_frequency is not None else 0.0),
            float(deployment.churn_ratio if deployment.churn_ratio is not None else 0.0),
            float(deployment.commit_density if deployment.commit_density is not None else 0.0),
            float(deployment.failure_rate_last_10 if deployment.failure_rate_last_10 is not None else 0.0),
            float(deployment.avg_risk_last_5 if deployment.avg_risk_last_5 is not None else 0.0),
            float(has_db_migration),
            float(has_auth_changes),
            float(has_payment_changes),
            float(has_core_module_changes)
        ]
        
        return features
        
    def _hash_features(self, features: List[float]) -> str:
        """Creates a stable hash indicating the exact state vector passed."""
        features_str = ",".join([f"{f:.4f}" for f in features])
        return hashlib.sha256(features_str.encode()).hexdigest()

    def train_model(self, db: Session) -> Dict[str, Any]:
        """Trains ML model using locked concurrency guards."""
        if not self._train_lock.acquire(blocking=False):
            logger.warning("[ML] train_bypassed=True reason=locked")
            return {"status": "error", "message": "Model is already actively training."}
            
        try:
            logger.info("[ML] train_start=True")
            past_deployments = db.query(Deployment).filter(
                Deployment.deployment_outcome.isnot(None)
            ).all()
            
            if len(past_deployments) < 30: # Upgraded to 30 for safety
                logger.warning(f"[ML] train_bypassed=True reason=insufficient_data samples={len(past_deployments)}")
                return {"status": "error", "message": f"Insufficient data to train model. Need 30 records, have {len(past_deployments)}."}
                
            X = []
            y = []
            
            for dep in past_deployments:
                outcome = str(dep.deployment_outcome).lower()
                if outcome in ["failure", "error", "rollback", "failed"]:
                    label = 1
                elif outcome in ["success", "completed"]:
                    label = 0
                else:
                    continue 
                    
                X.append(self.prepare_features(dep))
                y.append(label)
                
            if len(set(y)) < 2:
                logger.warning("[ML] train_bypassed=True reason=uniform_data_set")
                return {"status": "error", "message": "Insufficient variance in training labels. Both success and failure records are required."}
                
            pipeline = Pipeline([
                ('scaler', StandardScaler()),
                ('classifier', LogisticRegression(class_weight='balanced', random_state=42))
            ])
            pipeline.fit(X, y)
            self.model = pipeline
            
            # Metadata Management System
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            version_filename = f"risk_model_{timestamp}.pkl"
            meta_filename = f"risk_model_{timestamp}.meta.json"
            
            save_path = os.path.join(MODELS_DIR, version_filename)
            meta_path = os.path.join(MODELS_DIR, meta_filename)
            
            joblib.dump(self.model, save_path)
            
            self.current_version = version_filename
            self.current_metadata = {
                "model_version": self.current_version,
                "created_at": datetime.utcnow().isoformat(),
                "samples_trained": len(y),
                "features_used": FEATURE_NAMES,
                "model_type": "LogisticRegression"
            }
            
            with open(meta_path, "w") as f:
                json.dump(self.current_metadata, f, indent=4)
                
            logger.info(f"[ML] train_complete=True version={self.current_version} samples={len(y)}")
            return {
                "status": "success",
                "message": "Model trained successfully.",
                "version": self.current_version,
                "samples_trained": len(y)
            }
            
        finally:
            self._train_lock.release()
            
    def _explain_prediction(self, features: List[float], probabilities: Any) -> List[str]:
        """Provide XAI (Explainable AI) interpretation using LR coefficients."""
        if not self.model:
            return []
            
        scaler = self.model.named_steps['scaler']
        classifier = self.model.named_steps['classifier']
        
        try:
            # We need the coefficients corresponding to the failure class (index 1 usually)
            if classifier.classes_[1] == 1:
                coefs = classifier.coef_[0]
            else:
                coefs = -classifier.coef_[0]
        except Exception:
            return []
            
        scaled_features = scaler.transform([features])[0]
        
        # Calculate individual feature contributions (magnitude direction towards failure)
        contributions = []
        for i, (fname, scaled_val, coef_val) in enumerate(zip(FEATURE_NAMES, scaled_features, coefs)):
            impact = float(scaled_val * coef_val)
            if impact > 0: # We only care about things pushing it towards failure
                contributions.append((fname, impact))
                
        # Sort and return top 2
        contributions.sort(key=lambda x: x[1], reverse=True)
        top_factors = []
        for fname, impact in contributions[:2]:
            display_name = fname.replace("_", " ").title()
            # Normalize impact float to look clean (limit to 1 decimal normally)
            top_factors.append(f"ML identified {display_name} as a major failure indicator (+{impact:.1f})")
            
        return top_factors

    def predict_risk(self, deployment: Deployment) -> Tuple[float, str, float, List[str]]:
        """
        Predicts deployment risk using the configured ML pipeline.
        Returns: risk_score, risk_level, failure_probability, top_risk_factors
        """
        if not self.model:
            raise RuntimeError("ML Model is not loaded or does not exist.")
            
        features = self.prepare_features(deployment)
        
        # Record consistency signature
        deployment.feature_signature = self._hash_features(features)
        
        probabilities = self.model.predict_proba([features])[0]
        raw_failure_prob = probabilities[1] if self.model.classes_[1] == 1 else probabilities[0]
        
        failure_prob = min(max(raw_failure_prob, 0.05), 0.95)
        ml_risk_score = round(failure_prob * 100.0, 2)
        
        if failure_prob >= 0.70:
            ml_risk_level = "HIGH"
        elif failure_prob >= 0.40:
            ml_risk_level = "MEDIUM"
        else:
            ml_risk_level = "LOW"
            
        # Get XAI explanations
        top_factors = self._explain_prediction(features, probabilities)
        
        logger.info(f"[ML] prediction_cycle=Complete version={self.current_version} score={ml_risk_score} drift=0 confidence={float(abs(0.5 - failure_prob) * 2.0):.2f}")
            
        return ml_risk_score, ml_risk_level, failure_prob, top_factors

ml_engine = MLEngine()


def analyze_prediction_error(db: Session, limit: int = 50) -> dict:
    """
    Phase 9.2: Compute rolling classification metrics over last `limit` evaluated deployments.
    Returns accuracy, precision, recall, and per-class counts (TP/TN/FP/FN).
    """
    from ..models.deployment import Deployment as DeploymentModel

    evaluated = (
        db.query(DeploymentModel)
        .filter(
            DeploymentModel.prediction_correct.isnot(None),
            DeploymentModel.actual_outcome.isnot(None),
            DeploymentModel.predicted_failure.isnot(None),
        )
        .order_by(DeploymentModel.timestamp.desc())
        .limit(limit)
        .all()
    )

    if not evaluated:
        return {
            "insufficient_data": True,
            "evaluated_count": 0,
            "accuracy": None,
            "precision": None,
            "recall": None,
            "tp": 0, "tn": 0, "fp": 0, "fn": 0,
        }

    tp = sum(1 for d in evaluated if d.predicted_failure and d.actual_outcome)
    tn = sum(1 for d in evaluated if not d.predicted_failure and not d.actual_outcome)
    fp = sum(1 for d in evaluated if d.predicted_failure and not d.actual_outcome)
    fn = sum(1 for d in evaluated if not d.predicted_failure and d.actual_outcome)
    total = len(evaluated)

    accuracy  = round((tp + tn) / total, 4) if total > 0 else None
    precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else None
    recall    = round(tp / (tp + fn), 4) if (tp + fn) > 0 else None

    logger.info(
        f"[ML:9.2] metrics_computed evaluated={total} "
        f"accuracy={accuracy} precision={precision} recall={recall} "
        f"TP={tp} TN={tn} FP={fp} FN={fn}"
    )

    return {
        "insufficient_data": False,
        "evaluated_count": total,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "tp": tp, "tn": tn, "fp": fp, "fn": fn,
    }


def get_adaptive_thresholds(db: Session, limit: int = 50) -> dict:
    """
    Phase 9.2: Derive dynamic risk block/allow thresholds based on rolling precision/recall.
    Returns adjusted thresholds and a human-readable explanation list.
    """
    from ..config import settings
    base_block = settings.RISK_BLOCK_THRESHOLD
    base_allow = settings.RISK_ALLOW_THRESHOLD
    base_ml_block = 0.80

    metrics = analyze_prediction_error(db, limit=limit)
    reasons = []

    if metrics["insufficient_data"]:
        return {
            "risk_block_threshold": base_block,
            "risk_allow_threshold": base_allow,
            "ml_block_probability": base_ml_block,
            "adaptation_active": False,
            "reasons": ["Insufficient feedback data — using baseline thresholds."],
        }

    precision = metrics["precision"]
    recall    = metrics["recall"]
    adaptation_active = False

    adjusted_block = base_block
    adjusted_allow = base_allow
    adjusted_ml_block = base_ml_block

    # Too many False Positives → model too strict → relax thresholds
    if precision is not None and precision < 0.65:
        adjusted_block    = min(base_block + 5.0, 85.0)
        adjusted_ml_block = min(base_ml_block + 0.05, 0.90)
        adaptation_active = True
        reasons.append(
            f"Adaptive Policy: Low precision ({precision:.2f}) detected — "
            f"thresholds relaxed to reduce false blocks (block→{adjusted_block}, "
            f"ml_prob→{adjusted_ml_block:.2f})."
        )

    # Too many False Negatives → model too lenient → tighten thresholds
    if recall is not None and recall < 0.70:
        adjusted_block    = max(base_block - 5.0, 55.0)
        adjusted_ml_block = max(base_ml_block - 0.10, 0.65)
        adaptation_active = True
        reasons.append(
            f"Adaptive Policy: Low recall ({recall:.2f}) detected — "
            f"thresholds tightened to prevent missed failures (block→{adjusted_block}, "
            f"ml_prob→{adjusted_ml_block:.2f})."
        )

    if not reasons:
        reasons.append(
            f"Adaptive Policy: Metrics healthy (precision={precision:.2f}, "
            f"recall={recall:.2f}) — baseline thresholds retained."
        )

    return {
        "risk_block_threshold": adjusted_block,
        "risk_allow_threshold": adjusted_allow,
        "ml_block_probability": adjusted_ml_block,
        "adaptation_active": adaptation_active,
        "reasons": reasons,
    }
