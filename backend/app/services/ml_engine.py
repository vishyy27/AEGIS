import os
import joblib
from typing import Dict, Any, Tuple, Optional, List
from sqlalchemy.orm import Session
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from ..models.deployment import Deployment

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "ml", "risk_model.pkl")

# Ensure the ml directory exists
os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

class MLEngine:
    def __init__(self):
        self.model: Optional[Pipeline] = None
        self.load_model()
        
    def load_model(self) -> bool:
        """Loads the trained model pipeline from disk if available."""
        if os.path.exists(MODEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
                return True
            except Exception as e:
                print(f"Error loading ML model: {e}")
                self.model = None
        return False
        
    def prepare_features(self, deployment: Deployment) -> List[float]:
        """Extracts and formats features for the ML model from a Deployment object."""
        return [
            float(deployment.commit_count or 0),
            float(deployment.files_changed or 0),
            float(deployment.code_churn or 0),
            float(deployment.test_coverage or 100.0),
            float(deployment.dependency_updates or 0),
            float(deployment.historical_failures or 0),
            float(deployment.deployment_frequency or 0),
            float(deployment.churn_ratio or 0.0),
            float(deployment.commit_density or 0.0)
        ]

    def _dict_to_features(self, intelligence: Dict[str, Any], data: Dict[str, Any]) -> List[float]:
        """Convert intelligence and request data into feature array for prediction."""
        return [
            float(data.get("commit_count", 0)),
            float(data.get("files_changed", 0)),
            float(data.get("code_churn", 0)),
            float(data.get("test_coverage", 100.0)),
            float(data.get("dependency_updates", 0)),
            float(data.get("historical_failures", 0)),
            float(data.get("deployment_frequency", 0)),
            float(intelligence.get("churn_ratio", 0.0)),
            float(intelligence.get("commit_density", 0.0))
        ]

    def train_model(self, db: Session) -> Dict[str, Any]:
        """Trains the LogisticRegression model using historical deployment data."""
        # Query deployments that have an outcome (binary classification requirement)
        # Assuming explicit success/failure markers from Phase 7 are populated
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
                continue # Skip unknown states
                
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
        
        # Save model
        joblib.dump(self.model, MODEL_PATH)
        
        return {
            "status": "success",
            "message": "Model trained successfully.",
            "samples_trained": len(y)
        }

    def predict_risk(self, intelligence: Dict[str, Any], request_data: Dict[str, Any]) -> Tuple[float, str, float]:
        """
        Predicts deployment risk using the configured ML pipeline.
        Returns: Tuple of (ml_risk_score, ml_risk_level, failure_probability)
        """
        if not self.model:
            raise RuntimeError("ML Model is not loaded or does not exist.")
            
        features = self._dict_to_features(intelligence, request_data)
        
        # We need to reshape as predict_proba expects a 2D array
        probabilities = self.model.predict_proba([features])[0]
        
        # LogisticRegression classes_ are typically [0, 1] meaning probabilities[1] is chance of failure
        # To be safe against potential class ordering swap, we assume binary classification [0,1]
        failure_prob = probabilities[1] if self.model.classes_[1] == 1 else probabilities[0]
        
        ml_risk_score = round(failure_prob * 100.0, 2)
        
        # Define Risk Levels based on Thresholds
        if failure_prob >= 0.70:
            ml_risk_level = "HIGH"
        elif failure_prob >= 0.40:
            ml_risk_level = "MEDIUM"
        else:
            ml_risk_level = "LOW"
            
        return ml_risk_score, ml_risk_level, failure_prob

ml_engine = MLEngine()
