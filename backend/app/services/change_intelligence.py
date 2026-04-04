from typing import Dict, Any, List


def detect_sensitive_files(files: List[str]) -> List[str]:
    sensitive_keywords = [
        "auth",
        "config",
        "db",
        "payment",
        "credentials",
        "secret",
        "Dockerfile",
        "docker-compose",
    ]
    sensitive_files = []
    for file in files:
        if any(keyword in file.lower() for keyword in sensitive_keywords):
            sensitive_files.append(file)
    return sensitive_files


def calculate_churn_risk(added: int, deleted: int, file_count: int) -> float:
    if file_count <= 0:
        return 0.0
    total_churn = added + deleted
    # High massive change in few files is risky. High delete without add is risky script behaviour.
    density = total_churn / file_count

    risk_score = 0.0
    if density > 100:
        risk_score += min((density - 100) / 100 * 50, 50)

    if total_churn > 0:
        delete_ratio = deleted / total_churn
        if delete_ratio > 0.8:  # 80%+ deletion
            risk_score += 50
    return min(risk_score, 100.0)


def calculate_commit_density(churn: int, commits: int) -> float:
    if commits <= 0:
        return 0.0

    # 500 lines per commit is very suspicious (monolithic commit)
    lines_per_commit = churn / commits
    if lines_per_commit > 300:
        return min((lines_per_commit - 300) / 100 * 100, 100.0)
    return 0.0


def analyze_code_changes(data: Dict[str, Any]) -> Dict[str, Any]:
    # Defensive processing parsing
    files_changed = data.get("changed_files", []) or []
    commit_messages = data.get("commit_messages", []) or []
    lines_added = data.get("lines_added", 0) or 0
    lines_deleted = data.get("lines_deleted", 0) or 0
    commit_count = data.get("commit_count", 0) or 0
    code_churn = data.get("code_churn", 0) or 0
    dependency_updates = data.get("dependency_updates", 0) or 0
    file_count = data.get("files_changed", 0) or 0

    sensitive_found = detect_sensitive_files(files_changed)
    churn_risk_score = calculate_churn_risk(lines_added, lines_deleted, file_count)
    commit_density_score = calculate_commit_density(code_churn, commit_count)

    # Dependency 15%
    dep_score = min(dependency_updates / 3 * 100, 100)

    # Sensitive files maxes out bucket. 40%
    sensitive_score = min(len(sensitive_found) / 2 * 100, 100)

    # Weights calculation max 100
    change_risk_score = (
        sensitive_score * 0.40
        + churn_risk_score * 0.30
        + commit_density_score * 0.15
        + dep_score * 0.15
    )
    change_risk_score = round(min(max(change_risk_score, 0), 100), 2)

    # Derive risk categories
    risk_categories = []
    if sensitive_found:
        risk_categories.append("Sensitive file modifications")
    if (
        lines_deleted > 0
        and (lines_deleted / max((lines_added + lines_deleted), 1)) > 0.8
    ):
        risk_categories.append("Massive code deletion pattern")
    if commit_density_score > 50:
        risk_categories.append("Unsegmented monolithic commit")
    if (
        "bump" in str(commit_messages).lower()
        or "update" in str(commit_messages).lower()
    ):
        risk_categories.append("Blind dependency bump detected")

    ch_ratio = round(lines_deleted / max((lines_added + lines_deleted), 1), 2)
    c_density = round(code_churn / max(commit_count, 1), 2)

    return {
        "change_risk_score": change_risk_score,
        "risk_categories": risk_categories,
        "sensitive_files": sensitive_found,
        "churn_ratio": ch_ratio,
        "commit_density": c_density,
    }
