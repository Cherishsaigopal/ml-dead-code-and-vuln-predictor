from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from src.integration.enforcement import EnforcementDecision
from src.integration.predictor import PredictionResult
from src.integration.risk_scorer import RiskScoreResult


class AlertFormatter:
    """
    Generates explainable compiler/security alerts.
    """

    def _collect_indicators(self, pred: PredictionResult) -> List[str]:
        f = pred.features_used
        indicators: List[str] = []

        if f.get("cyclomatic", 0) >= 10:
            indicators.append("High cyclomatic complexity")
        if f.get("max_nesting_depth", 0) >= 4:
            indicators.append("Deep nesting depth")
        if f.get("sensitive_api_calls", 0) > 0:
            indicators.append("Sensitive API usage detected")
        if f.get("high_risk_api_flag", 0) > 0:
            indicators.append("High-risk API flag triggered")
        if f.get("unreachable_blocks", 0) > 0:
            indicators.append("Unreachable blocks detected")
        if f.get("loc", 0) >= 80:
            indicators.append("Large function size")
        if f.get("churn", 0) >= 10:
            indicators.append("High code churn")
        if f.get("commit_count", 0) >= 20:
            indicators.append("Frequently modified code region")

        if not indicators:
            indicators.append("No major static indicators exceeded rule thresholds")

        return indicators

    def format_console_alert(
        self,
        pred: PredictionResult,
        risk: RiskScoreResult,
        decision: EnforcementDecision,
    ) -> str:
        indicators = self._collect_indicators(pred)

        lines = [
            "=" * 72,
            "SECURITY ALERT",
            "-" * 72,
            f"File                 : {pred.file}",
            f"Function             : {pred.function_name}",
            f"Function ID          : {pred.function_id}",
            f"Dead Code Probability: {pred.dead_prob:.4f}",
            f"Vuln Probability     : {pred.vuln_prob:.4f}",
            f"Dead Risk            : {risk.dead_risk.upper()}",
            f"Vuln Risk            : {risk.vuln_risk.upper()}",
            f"Overall Risk         : {risk.overall_risk.upper()}",
            f"Compiler Action      : {decision.action.upper()}",
            f"Reason               : {decision.reason}",
            "Indicators           :",
        ]

        for item in indicators:
            lines.append(f"  - {item}")

        return "\n".join(lines)

    def format_json_record(
        self,
        pred: PredictionResult,
        risk: RiskScoreResult,
        decision: EnforcementDecision,
    ) -> Dict:
        return {
            "file": pred.file,
            "function_name": pred.function_name,
            "function_id": pred.function_id,
            "dead_probability": pred.dead_prob,
            "vulnerability_probability": pred.vuln_prob,
            "dead_risk": risk.dead_risk,
            "vulnerability_risk": risk.vuln_risk,
            "overall_risk": risk.overall_risk,
            "action": decision.action,
            "reason": decision.reason,
            "indicators": self._collect_indicators(pred),
            "features_used": pred.features_used,
        }

    def save_json_report(self, records: List[Dict], output_path: str) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)

    def save_text_report(self, alerts: List[str], output_path: str) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(alerts))