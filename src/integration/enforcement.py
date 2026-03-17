from __future__ import annotations

from dataclasses import dataclass
from typing import List

from src.integration.risk_scorer import RiskScoreResult


@dataclass
class EnforcementDecision:
    function_id: str
    function_name: str
    file: str
    action: str
    reason: str
    overall_risk: str


class SecurityEnforcer:
    """
    Maps risk levels to compiler-style actions.
    """

    def decide(self, risk: RiskScoreResult) -> EnforcementDecision:
        if risk.overall_risk == "critical":
            return EnforcementDecision(
                function_id=risk.function_id,
                function_name=risk.function_name,
                file=risk.file,
                action="block",
                reason="Critical vulnerability risk exceeds allowed threshold.",
                overall_risk=risk.overall_risk,
            )

        if risk.overall_risk == "high":
            return EnforcementDecision(
                function_id=risk.function_id,
                function_name=risk.function_name,
                file=risk.file,
                action="flag",
                reason="High-risk suspicious code detected and flagged for review.",
                overall_risk=risk.overall_risk,
            )

        if risk.overall_risk == "medium":
            return EnforcementDecision(
                function_id=risk.function_id,
                function_name=risk.function_name,
                file=risk.file,
                action="warn",
                reason="Moderate risk detected; compilation allowed with warning.",
                overall_risk=risk.overall_risk,
            )

        return EnforcementDecision(
            function_id=risk.function_id,
            function_name=risk.function_name,
            file=risk.file,
            action="allow",
            reason="No significant security risk detected.",
            overall_risk=risk.overall_risk,
        )

    def summarize_file_decision(self, decisions: List[EnforcementDecision]) -> str:
        """
        Final file-level decision:
          if any block -> block
          elif any flag -> flag
          elif any warn -> warn
          else allow
        """
        actions = {d.action for d in decisions}

        if "block" in actions:
            return "block"
        if "flag" in actions:
            return "flag"
        if "warn" in actions:
            return "warn"
        return "allow"