import os
import joblib
import glob
import json
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List
from sqlalchemy.orm import Session
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from ..models.deployment import Deployment

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "ml", "models")
os.makedirs(MODELS_DIR, exist_ok=True)

class MLEngine:
    def __init__(self):
        self.model: Optional[Pipeline] = None
        self.current_version: Optional[str] = None
        self.load_model()
        
    def load_model(self) -> bool:
        """Loads the most recent trained model pipeline from disk."""
        model_files = glob.glob(os.path.join(MODELS_DIR, "risk_model_*.pkl"))
        if not model_files:
            self.model = None
            self.current_version = None
            return False
            
        # Sort by filename descending (relying on timestamp naming convention)
        model_files.sort(reverse=True)
        latest_model = model_files[0]
        
        try:
            self.model = joblib.load(latest_model)
            self.current_version = os.path.basename(latest_model)
            return True
        except Exception as e:
            print(f"Error loading ML model {latest_model}: {e}")
            self.model = None
            self.current_version = None
            return False
            
    def prepare_features(self, deployment: Deployment) -> List[float]:
        """Extracts and formats features for the ML model from a Deployment object."""
        # Clean sensitive_files
        sensitive_files = []
        if deployment.sensitive_files:
            try:
                if isinstance(deployment.sensitive_files, str):
                    sensitive_files = json.loads(deployment.sensitive_files)
                elif isinstance(deployment.sensitive_files, list):
                    sensitive_files = deployment.sensitive_files
            except json.JSONDecodeError:
                pass
                
        # Parse logic for specific changes
        has_db_migration = deployment.has_db_migration or any("db" in f.lower() for f in sensitive_files)
        has_auth_changes = deployment.has_auth_changes or any("auth" in f.lower() for f in sensitive_files)
        has_payment_changes = deployment.has_payment_changes or any("payment" in f.lower() for f in sensitive_files)
        has_core_module_changes = deployment.has_core_module_changes or any("config" in f.lower() for f in sensitive_files)
        
        # In case we update the object directly here before inference
        deployment.has_db_migration = has_db_migration
        deployment.has_auth_changes = has_auth_changes
        deployment.has_payment_changes = has_payment_changes
        deployment.has_core_module_changes = has_core_module_changes

        return [
            float(deployment.commit_count or 0),
            float(deployment.files_changed or 0),
            float(deployment.code_churn or 0),
            float(deployment.test_coverage or 100.0),
            float(deployment.dependency_updates or 0),
            float(deployment.historical_failures or 0),
            float(deployment.deployment_frequency or 0),
            float(deployment.churn_ratio or 0.0),
            float(deployment.commit_density or 0.0),
            float(deployment.failure_rate_last_10 or 0.0),
            float(deployment.avg_risk_last_5 or 0.0),
            float(has_db_migration),
            float(has_auth_changes),
            float(has_payment_changes),
            float(has_core_module_changes)
        ]

    def train_model(self, db: Session) -> Dict[str, Any]:
        """Trains the LogisticRegression model using historical deployment data."""
        past_deployments = db.query(Deployment).filter(
            Deployment.deployment_outcome.isnot(None)
        ).all()
        
        if len(past_deployments) < 10:
            return {"status": "error", "message": "Insufficient data to train model. Need at least 10 records."}
            
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
            return {"status": "error", "message": "Insufficient variance in training labels. Both success and failure records are required."}
            
        # Define pipeline: Scale features -> LogisticRegression
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('classifier', LogisticRegression(class_weight='balanced', random_state=42))
        ])
        
        pipeline.fit(X, y)
        self.model = pipeline
        
        # Save versioned model
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        version_filename = f"risk_model_{timestamp}.pkl"
        save_path = os.path.join(MODELS_DIR, version_filename)
        
        joblib.dump(self.model, save_path)
        self.current_version = version_filename
        
        return {
            "status": "success",
            "message": "Model trained successfully.",
            "version": self.current_version,
            "samples_trained": len(y)
        }

    def predict_risk(self, deployment: Deployment) -> Tuple[float, str, float]:
        """
        Predicts deployment risk using the configured ML pipeline.
        Applies probability clamping.
        """
        if not self.model:
            raise RuntimeError("ML Model is not loaded or does not exist.")
            
        features = self.prepare_features(deployment)
        probabilities = self.model.predict_proba([features])[0]
        
        raw_failure_prob = probabilities[1] if self.model.classes_[1] == 1 else probabilities[0]
        
        # Calibration Layer (Clamping values to prevent overconfidence)
        failure_prob = min(max(raw_failure_prob, 0.05), 0.95)
        
        ml_risk_score = round(failure_prob * 100.0, 2)
        
        if failure_prob >= 0.70:
            ml_risk_level = "HIGH"
        elif failure_prob >= 0.40:
            ml_risk_level = "MEDIUM"
        else:
            ml_risk_level = "LOW"
            
        return ml_risk_score, ml_risk_level, failure_prob

ml_engine = MLEngine()
