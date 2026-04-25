import sys
import os
import json
from datetime import datetime

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.database import SessionLocal
from backend.app.models.deployment import Deployment

def run_evaluation():
    print("Starting AEGIS Offline Evaluation...")
    db = SessionLocal()
    try:
        # Load all evaluated deployments
        evaluated = db.query(Deployment).filter(
            Deployment.prediction_correct.isnot(None),
            Deployment.actual_outcome.isnot(None)
        ).all()
        
        if not evaluated:
            print("No evaluated deployments found to benchmark.")
            return

        cnt = len(evaluated)
        print(f"Loaded {cnt} evaluated deployments for benchmarking.")

        # Metrics trackers
        def get_metrics_dict():
            return {"TP": 0, "TN": 0, "FP": 0, "FN": 0}
            
        sys_ml = get_metrics_dict()
        sys_rule = get_metrics_dict()
        sys_aegis = get_metrics_dict()

        for dep in evaluated:
            actual_failure = bool(dep.actual_outcome)
            
            # ML Only Prediction
            ml_pred = False
            if dep.ml_prediction_prob is not None:
                ml_pred = dep.ml_prediction_prob >= 0.5
            
            # Rule Based Prediction (assume risk >= 75 as block/fail)
            rule_pred = False
            if dep.risk_score is not None:
                rule_pred = dep.risk_score >= 75.0
                
            # AEGIS Hybrid Prediction (BLOCK = failure predicted)
            aegis_pred = dep.deployment_decision == "BLOCK"
            
            # Helper to score
            def score(pred, actual, metrics):
                if pred and actual: metrics["TP"] += 1
                elif not pred and not actual: metrics["TN"] += 1
                elif pred and not actual: metrics["FP"] += 1
                elif not pred and actual: metrics["FN"] += 1

            score(ml_pred, actual_failure, sys_ml)
            score(rule_pred, actual_failure, sys_rule)
            score(aegis_pred, actual_failure, sys_aegis)

        def calc_stats(name, m):
            tp, tn, fp, fn = m["TP"], m["TN"], m["FP"], m["FN"]
            total = tp + tn + fp + fn
            accuracy = (tp + tn) / total if total > 0 else 0
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            return {
                "name": name,
                "accuracy": round(accuracy, 2),
                "precision": round(precision, 2),
                "recall": round(recall, 2),
                "f1": round(f1, 2)
            }

        res_ml = calc_stats("ML Only", sys_ml)
        res_rule = calc_stats("Rule Based", sys_rule)
        res_aegis = calc_stats("AEGIS Hybrid", sys_aegis)
        
        # Determine winner
        systems = [res_ml, res_rule, res_aegis]
        winner = max(systems, key=lambda x: x["f1"])

        print("\nBenchmarking Results:")
        print(f"{'System':<15} {'Accuracy':<10} {'Precision':<10} {'Recall':<10} {'F1':<10}")
        print("─" * 55)
        for s in systems:
            win_str = "   ← winner" if s["name"] == winner["name"] else ""
            print(f"{s['name']:<15} {s['accuracy']:<10.2f} {s['precision']:<10.2f} {s['recall']:<10.2f} {s['f1']:<10.2f}{win_str}")

        # Save report
        os.makedirs("backend/reports", exist_ok=True)
        report_path = f"backend/reports/evaluation_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "evaluated_count": cnt,
            "metrics": {
                "ml_only": res_ml,
                "rule_based": res_rule,
                "aegis_hybrid": res_aegis
            },
            "raw_counts": {
                "ml_only": sys_ml,
                "rule_based": sys_rule,
                "aegis_hybrid": sys_aegis
            }
        }
        
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
            
        print(f"\nReport saved to: {report_path}")

    finally:
        db.close()

if __name__ == "__main__":
    run_evaluation()
