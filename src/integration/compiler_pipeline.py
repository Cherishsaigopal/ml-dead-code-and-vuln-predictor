from __future__ import annotations

import hashlib
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from src.integration.alert_formatter import AlertFormatter
from src.integration.enforcement import EnforcementDecision, SecurityEnforcer
from src.integration.predictor import ModelPredictor, PredictionResult
from src.integration.risk_scorer import RiskScoreResult, RiskScorer


@dataclass
class PipelineOutput:
    file_path: str
    file_decision: str
    prediction_results: List[PredictionResult]
    risk_results: List[RiskScoreResult]
    enforcement_results: List[EnforcementDecision]
    alerts: List[str]
    json_records: List[Dict]


@dataclass
class SimpleFunctionInfo:
    function_id: str
    function_name: str
    file: str
    start_line: int
    end_line: int
    code: str


class SecureCompilerPipeline:
    """
    Week 10 secure compilation pipeline.

    Current design:
    - Works immediately on real .cpp files
    - Uses lightweight source parsing inside this file
    - Matches your trained model feature names
    - Leaves clean hook points for your real Week 7–9 modules later

    Existing project files seen in your structure:
    - src/Parser/clang_parser.py
    - src/cfg/builder.py
    - src/analysis/reachability.py
    - src/analysis/dead_code.py
    - src/features/extract.py
    - scripts/compute_commit_count.py
    """

    def __init__(self, model_dir: str = "models") -> None:
        self.predictor = ModelPredictor(model_dir=model_dir)
        self.risk_scorer = RiskScorer()
        self.enforcer = SecurityEnforcer()
        self.formatter = AlertFormatter()

    def run(self, file_path: str) -> PipelineOutput:
        file_path = str(Path(file_path).resolve())

        features_df = self._extract_features_from_file(file_path)
        if features_df.empty:
            raise ValueError(f"No functions/features extracted from file: {file_path}")

        prediction_results = self.predictor.predict_dataframe(features_df)

        risk_results: List[RiskScoreResult] = []
        enforcement_results: List[EnforcementDecision] = []
        alerts: List[str] = []
        json_records: List[Dict] = []

        for pred in prediction_results:
            risk = self.risk_scorer.score_prediction(pred)
            decision = self.enforcer.decide(risk)
            alert = self.formatter.format_console_alert(pred, risk, decision)
            record = self.formatter.format_json_record(pred, risk, decision)

            risk_results.append(risk)
            enforcement_results.append(decision)
            alerts.append(alert)
            json_records.append(record)

        file_decision = self.enforcer.summarize_file_decision(enforcement_results)

        return PipelineOutput(
            file_path=file_path,
            file_decision=file_decision,
            prediction_results=prediction_results,
            risk_results=risk_results,
            enforcement_results=enforcement_results,
            alerts=alerts,
            json_records=json_records,
        )

    def save_reports(self, result: PipelineOutput, output_dir: str = "outputs/week10") -> None:
        output_base = Path(output_dir)
        report_dir = output_base / "reports"
        flagged_dir = output_base / "flagged_samples"

        safe_name = Path(result.file_path).stem

        text_path = report_dir / f"{safe_name}_security_report.txt"
        json_path = report_dir / f"{safe_name}_security_report.json"

        self.formatter.save_text_report(result.alerts, str(text_path))
        self.formatter.save_json_report(result.json_records, str(json_path))

        if result.file_decision in {"warn", "flag", "block"}:
            sample_path = flagged_dir / f"{safe_name}_{result.file_decision}.txt"
            self.formatter.save_text_report(result.alerts, str(sample_path))

    # ------------------------------------------------------------------
    # Feature extraction
    # ------------------------------------------------------------------

    def _extract_features_from_file(self, file_path: str) -> pd.DataFrame:
        path = Path(file_path)
        code = path.read_text(encoding="utf-8", errors="ignore")

        functions = self._extract_functions(code, str(path))
        if not functions:
            functions = [
                SimpleFunctionInfo(
                    function_id=self._make_function_id(str(path), "file_scope", 1, max(1, len(code.splitlines()))),
                    function_name="file_scope",
                    file=str(path),
                    start_line=1,
                    end_line=max(1, len(code.splitlines())),
                    code=code,
                )
            ]

        repo_root = self._find_git_root(path)
        rows: List[Dict] = []

        for fn in functions:
            row = {
                "function_id": fn.function_id,
                "function_name": fn.function_name,
                "file": fn.file,
            }
            row.update(self._compute_function_features(fn, repo_root))
            rows.append(row)

        return pd.DataFrame(rows)

    def _extract_functions(self, code: str, file_path: str) -> List[SimpleFunctionInfo]:
        """
        Lightweight C/C++ function extractor.
        This avoids guessing APIs from your existing files.
        """
        text = code

        pattern = re.compile(
            r"""
            (?P<sig>
                (?:[A-Za-z_~][\w:<>,~*\s&]+?)
                \s+
                (?P<name>[A-Za-z_~]\w*)
                \s*
                \(
                    [^;{}()]* (?:\([^()]*\)[^;{}()]*)*
                \)
                (?:\s*(?:const|noexcept|override|final))*
            )
            \s*
            \{
            """,
            re.VERBOSE | re.MULTILINE,
        )

        functions: List[SimpleFunctionInfo] = []

        for match in pattern.finditer(text):
            name = match.group("name")
            if name in {"if", "for", "while", "switch", "catch"}:
                continue

            body_start = match.end() - 1
            body_end = self._find_matching_brace(text, body_start)
            if body_end is None:
                continue

            start_line = text[:match.start()].count("\n") + 1
            end_line = text[:body_end].count("\n") + 1
            fn_code = text[match.start():body_end + 1]

            functions.append(
                SimpleFunctionInfo(
                    function_id=self._make_function_id(file_path, name, start_line, end_line),
                    function_name=name,
                    file=file_path,
                    start_line=start_line,
                    end_line=end_line,
                    code=fn_code,
                )
            )

        return functions

    def _find_matching_brace(self, text: str, open_idx: int) -> Optional[int]:
        depth = 0
        in_string = False
        string_char = ""
        escape = False

        for i in range(open_idx, len(text)):
            ch = text[i]

            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == string_char:
                    in_string = False
                continue

            if ch in {'"', "'"}:
                in_string = True
                string_char = ch
                continue

            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return i

        return None

    def _compute_function_features(self, fn: SimpleFunctionInfo, repo_root: Optional[Path]) -> Dict[str, float]:
        code = self._strip_comments(fn.code)
        lines = [ln for ln in code.splitlines() if ln.strip()]

        loc = len(lines)
        branch_count = self._count_regex(code, r"\b(if|else\s+if|switch|case)\b") + code.count("?")
        loop_count = self._count_regex(code, r"\b(for|while|do)\b")
        return_count = self._count_regex(code, r"\breturn\b")
        call_count = self._count_function_calls(code)
        max_nesting_depth = self._max_brace_depth(code)

        cyclomatic = 1 + branch_count + loop_count + self._count_regex(code, r"&&|\|\|")

        sensitive_api_calls = self._count_sensitive_calls(code)
        high_risk_api_flag = 1 if sensitive_api_calls > 0 else 0

        basic_blocks = max(1, 1 + branch_count + loop_count + return_count)
        cfg_edges = max(1, basic_blocks + branch_count + loop_count)

        unreachable_blocks, unreachable_ratio = self._estimate_unreachable(code, basic_blocks)

        commit_count, churn = self._git_history_features(Path(fn.file), repo_root)

        return {
            "loc": float(loc),
            "cyclomatic": float(cyclomatic),
            "branch_count": float(branch_count),
            "loop_count": float(loop_count),
            "max_nesting_depth": float(max_nesting_depth),
            "call_count": float(call_count),
            "return_count": float(return_count),
            "basic_blocks": float(basic_blocks),
            "cfg_edges": float(cfg_edges),
            "sensitive_api_calls": float(sensitive_api_calls),
            "high_risk_api_flag": float(high_risk_api_flag),
            "commit_count": float(commit_count),
            "churn": float(churn),
            "unreachable_blocks": float(unreachable_blocks),
            "unreachable_ratio": float(unreachable_ratio),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _strip_comments(self, code: str) -> str:
        code = re.sub(r"//.*?$", "", code, flags=re.MULTILINE)
        code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)
        return code

    def _count_regex(self, text: str, pattern: str) -> int:
        return len(re.findall(pattern, text))

    def _count_function_calls(self, code: str) -> int:
        matches = re.findall(r"\b([A-Za-z_]\w*)\s*\(", code)
        ignore = {
            "if", "for", "while", "switch", "return", "sizeof", "catch",
            "static_cast", "dynamic_cast", "reinterpret_cast", "const_cast"
        }
        return sum(1 for m in matches if m not in ignore)

    def _max_brace_depth(self, code: str) -> int:
        depth = 0
        max_depth = 0
        for ch in code:
            if ch == "{":
                depth += 1
                max_depth = max(max_depth, depth)
            elif ch == "}":
                depth = max(0, depth - 1)
        return max_depth

    def _count_sensitive_calls(self, code: str) -> int:
        risky = [
            "strcpy", "strcat", "gets", "sprintf", "vsprintf", "scanf",
            "sscanf", "fscanf", "memcpy", "memmove", "malloc", "free",
            "system", "popen", "exec", "CreateProcess", "ShellExecute"
        ]
        total = 0
        for api in risky:
            total += len(re.findall(rf"\b{re.escape(api)}\s*\(", code))
        return total

    def _estimate_unreachable(self, code: str, basic_blocks: int) -> tuple[int, float]:
        lines = [ln.strip() for ln in code.splitlines() if ln.strip()]
        unreachable_signals = 0

        for i, line in enumerate(lines[:-1]):
            if re.search(r"\b(return|break|continue|throw)\b", line):
                nxt = lines[i + 1]
                if nxt not in {"}", "};"}:
                    unreachable_signals += 1

        unreachable_blocks = min(unreachable_signals, max(0, basic_blocks - 1))
        ratio = 0.0 if basic_blocks <= 0 else unreachable_blocks / basic_blocks
        return unreachable_blocks, ratio

    def _find_git_root(self, path: Path) -> Optional[Path]:
        current = path.parent.resolve()
        for candidate in [current, *current.parents]:
            if (candidate / ".git").exists():
                return candidate
        return None

    def _git_history_features(self, file_path: Path, repo_root: Optional[Path]) -> tuple[int, int]:
        if repo_root is None:
            return 0, 0

        try:
            rel_path = str(file_path.resolve().relative_to(repo_root.resolve()))
        except Exception:
            return 0, 0

        try:
            commit_cmd = [
                "git", "-C", str(repo_root), "log", "--follow", "--oneline", "--", rel_path
            ]
            commit_out = subprocess.run(commit_cmd, capture_output=True, text=True, check=False)

            commit_count = 0
            if commit_out.returncode == 0 and commit_out.stdout.strip():
                commit_count = len([ln for ln in commit_out.stdout.splitlines() if ln.strip()])

            churn_cmd = [
                "git", "-C", str(repo_root), "log", "--follow", "--numstat",
                "--pretty=tformat:", "--", rel_path
            ]
            churn_out = subprocess.run(churn_cmd, capture_output=True, text=True, check=False)

            churn = 0
            if churn_out.returncode == 0 and churn_out.stdout.strip():
                for line in churn_out.stdout.splitlines():
                    parts = line.strip().split()
                    if len(parts) >= 3 and parts[0].isdigit() and parts[1].isdigit():
                        churn += int(parts[0]) + int(parts[1])

            return commit_count, churn
        except Exception:
            return 0, 0

    def _make_function_id(self, file_path: str, function_name: str, start_line: int, end_line: int) -> str:
        raw = f"{file_path}:{function_name}:{start_line}:{end_line}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()[:16]