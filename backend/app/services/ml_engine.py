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
