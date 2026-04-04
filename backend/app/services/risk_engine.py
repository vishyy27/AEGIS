from typing import Dict, Any, Tuple, List


def calculate_risk_score(
    deployment_data: Dict[str, Any],
) -> Tuple[float, str, List[str]]:
    # Extract data
    code_churn = deployment_data.get("code_churn", 0)
    test_coverage = deployment_data.get("test_coverage", 100.0)
    historical_failures = deployment_data.get("historical_failures", 0)
    files_changed = deployment_data.get("files_changed", 0)
    dependency_updates = deployment_data.get("dependency_updates", 0)
    deployment_frequency = deployment_data.get("deployment_frequency", 0)
    commit_count = deployment_data.get("commit_count", 0)

    # Calculate Weights
    # Recalibrated Weights for realistic scale
    churn_score = min(code_churn / 150.0 * 100, 100)
    files_score = min(files_changed / 15.0 * 100, 100)
    coverage_score = min(max(0, (95.0 - test_coverage) / 20.0 * 100), 100)
    failure_score = min(historical_failures / 2.0 * 100, 100)
    dependency_score = min(dependency_updates / 4.0 * 100, 100)
    commit_score = min(commit_count / 10.0 * 100, 100)

    risk_score = (
        churn_score * 0.25
        + files_score * 0.15
        + coverage_score * 0.20
        + failure_score * 0.15
        + dependency_score * 0.15
        + commit_score * 0.10
    )

    risk_score = round(min(max(risk_score, 0.0), 100.0), 2)

    if risk_score >= 70.0:
        risk_level = "HIGH"
    elif risk_score >= 40.0:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # Determine risk factors using specific rules recalibrated
    risk_factors = []
    if code_churn > 100:
        risk_factors.append("High code churn")
    if test_coverage < 80:
        risk_factors.append("Low test coverage")
    if historical_failures > 1:
        risk_factors.append("Frequent historical failures")
    if files_changed > 10:
        risk_factors.append("Large number of files changed")
    if dependency_updates > 2:
        risk_factors.append("Multiple dependency updates")
    if deployment_frequency < 5:
        risk_factors.append("Low deployment frequency (Large release risk)")

    return round(risk_score, 2), risk_level, risk_factors
