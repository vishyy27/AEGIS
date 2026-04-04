export interface RiskResult {
  score: number;
  level: "LOW" | "MEDIUM" | "HIGH";
  confidence: number;
  suggestions: string[];
}

export const predictRisk = (params: {
  filesChanged: number;
  linesChanged: number;
  complexity: number;
  testCoverage: number;
}): RiskResult => {
  // Simple mock logic for demonstration
  const score = Math.min(
    100,
    Math.round(
      params.filesChanged * 0.5 +
        params.linesChanged * 0.01 +
        params.complexity * 0.6 -
        params.testCoverage * 0.3,
    ),
  );

  let level: "LOW" | "MEDIUM" | "HIGH" = "LOW";
  if (score > 70) level = "HIGH";
  else if (score > 30) level = "MEDIUM";

  const suggestions = [];
  if (params.testCoverage < 80)
    suggestions.push("Increase test coverage above 80%");
  if (params.complexity > 70)
    suggestions.push("Refactor large functions to reduce complexity");
  if (params.filesChanged > 50)
    suggestions.push("Split large PR into smaller atomic deployments");

  return {
    score,
    level,
    confidence: 85 + Math.random() * 10,
    suggestions:
      suggestions.length > 0 ? suggestions : ["Safely proceed with deployment"],
  };
};
