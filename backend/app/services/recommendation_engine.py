def generate_recommendations(risk_factors: list[str]) -> list[str]:
    recommendations = []

    rules = {
        "High code churn": "split deployment",
        "Low test coverage": "improve testing",
        "Multiple dependency updates": "dependency audit",
        "Frequent historical failures": "Review previous incident post-mortems and test edge cases.",
        "Large number of files changed": "Conduct a thorough peer review focusing on architectural impacts.",
        "Low deployment frequency (Large release risk)": "Ensure automated rollback capabilities are fully functional.",
    }

    for factor in risk_factors:
        if factor in rules:
            recommendations.append(rules[factor])

    if not recommendations and not risk_factors:
        recommendations.append("Safe to deploy. Continue standard monitoring.")

    return recommendations
