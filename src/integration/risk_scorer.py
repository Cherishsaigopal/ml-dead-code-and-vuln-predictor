from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from src.integration.predictor import PredictionResult


@dataclass
class RiskScoreResult:
    function_id: str
    function_name: str
    file: str

    dead_prob: float
    vuln_prob: float

    dead_risk: str
    vuln_risk: str
    overall_risk: str

    score: float


class RiskScorer:
    """
    Converts model probabilities into human-readable risk levels.
    """

    def __init__(
        self,
        dead_medium: float = 0.15,      # LOWERED from 0.40
        dead_high: float = 0.35,        # LOWERED from 0.70
        vuln_medium: float = 0.15,      # LOWERED from 0.30 (your outputs are 0.007-0.19)
        vuln_high: float = 0.30,        # LOWERED from 0.60
        vuln_critical: float = 0.50,
    ) -> None:
        self.dead_medium = dead_medium
        self.dead_high = dead_high
        self.vuln_medium = vuln_medium
        self.vuln_high = vuln_high
        self.vuln_critical = vuln_critical

    def _dead_risk(self, p: float) -> str:
        if p >= self.dead_high:
            return "high"
        if p >= self.dead_medium:
            return "medium"
        return "low"

    def _vuln_risk(self, p: float) -> str:
        if p >= self.vuln_critical:
            return "critical"
        if p >= self.vuln_high:
            return "high"
        if p >= self.vuln_medium:
            return "medium"
        return "low"

    def _overall_risk(self, dead_risk: str, vuln_risk: str) -> str:
        # vulnerability takes priority
        if vuln_risk == "critical":
            return "critical"
        if vuln_risk == "high":
            return "high"
        if dead_risk == "high":
            return "high"
        if vuln_risk == "medium" or dead_risk == "medium":
            return "medium"
        return "low"

    def _combined_score(self, dead_prob: float, vuln_prob: float) -> float:
        # give more weight to vulnerability
        return (0.35 * dead_prob) + (0.65 * vuln_prob)

    def score_prediction(self, pred: PredictionResult) -> RiskScoreResult:
        dead_risk = self._dead_risk(pred.dead_prob)
        vuln_risk = self._vuln_risk(pred.vuln_prob)
        overall_risk = self._overall_risk(dead_risk, vuln_risk)
        score = self._combined_score(pred.dead_prob, pred.vuln_prob)

        return RiskScoreResult(
            function_id=pred.function_id,
            function_name=pred.function_name,
            file=pred.file,
            dead_prob=pred.dead_prob,
            vuln_prob=pred.vuln_prob,
            dead_risk=dead_risk,
            vuln_risk=vuln_risk,
            overall_risk=overall_risk,
            score=score,
        )