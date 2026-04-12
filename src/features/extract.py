import re
from dataclasses import dataclass, asdict
from typing import Dict, Set

from ..cfg.models import CFG
from ..utils.log import get_logger

log = get_logger(__name__)

SENSITIVE_APIS = {
    "strcpy", "strcat", "gets", "sprintf", "vsprintf",
    "memcpy", "scanf", "sscanf", "system", "popen",
}

HIGH_RISK_APIS = {
    "gets", "strcpy", "sprintf", "vsprintf", "system",
    "sscanf", "memcpy", "popen" 
}

@dataclass
class FeatureRow:
    sample_id: str
    file_name: str
    function_name: str

    loc: int
    cyclomatic: int
    branch_count: int
    loop_count: int
    max_nesting_depth: int
    call_count: int
    return_count: int

    basic_blocks: int
    cfg_edges: int
    unreachable_blocks: int
    unreachable_ratio: float

    sensitive_api_calls: int
    high_risk_api_flag: int

    commit_count: int
    churn: int

def _max_depth_stmt(node, depth: int) -> int:
    best = depth
    increment = 1 if node.kind in ("if", "for", "while", "do", "compound") else 0
    for ch in node.children:
        best = max(best, _max_depth_stmt(ch, depth + increment))
    return best

def _count_kinds_in_cfg(cfg: CFG, kinds: Set[str]) -> int:
    c = 0
    for b in cfg.blocks.values():
        for k in b.stmt_kinds:
            if k in kinds:
                c += 1
    return c

def _read_source_code(file_path: str, start_line: int, end_line: int) -> str:
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        source_lines = lines[start_line-1:end_line]
        return "".join(source_lines)
    except Exception as e:
        log.warning(f"Could not read source file {file_path}: {e}")
        return ""

def _count_sensitive_from_source(source_code: str) -> tuple[int, int]:
    sensitive_api_calls = 0
    high_risk_api_flag = 0
    if not source_code:
        return 0, 0
    
    for api in SENSITIVE_APIS:
        pattern = rf"\b{re.escape(api)}\s*\("
        matches = re.findall(pattern, source_code, re.IGNORECASE)
        if matches:
            sensitive_api_calls += len(matches)
    
    for api in HIGH_RISK_APIS:
        pattern = rf"\b{re.escape(api)}\s*\("
        matches = re.findall(pattern, source_code, re.IGNORECASE)
        if matches:
            high_risk_api_flag = 1
            
    return sensitive_api_calls, high_risk_api_flag

def _count_dead_code_heuristics(source_code: str) -> int:
    """Accurately detects unused local variables and structurally unreachable code."""
    lines = [ln.strip() for ln in source_code.splitlines() if ln.strip()]
    dead_count = 0
    
    # 1. Structural dead code (code physically placed after an unconditional return/break)
    for i, line in enumerate(lines[:-1]):
        # re.match ensures it STARTS with return/break. It ignores `if (...) return;`
        if re.match(r"^(return|break|continue|throw)\b", line):
            nxt = lines[i + 1]
            # If the next line isn't just a closing bracket, it's dead code!
            if nxt not in {"}", "};", "break;", "continue;"}:
                dead_count += 1
                
    # 2. Unused variables
    for i, line in enumerate(lines):
        # Skip loop/if definitions entirely
        if line.startswith("for") or line.startswith("while") or line.startswith("if"):
            continue
            
        # Match standard standalone variable declarations (e.g. int x = 5; char buf[10];)
        match = re.search(r"\b(?:const\s+)?(?:int|char|float|double|bool|auto)\s*\*?\s+([a-zA-Z_]\w*)\s*(?:=|\[|;)", line)
        
        if match:
            var_name = match.group(1)
            is_used = False
            
            # Search subsequent lines for usage
            for future_line in lines[i+1:]:
                if future_line in ["}", "};"]:
                    continue
                # Ensure variable is used as a whole word
                if re.search(rf"\b{var_name}\b", future_line):
                    is_used = True
                    break
            
            if not is_used:
                dead_count += 1
                
    return dead_count

def extract_features_from_cfg(
    sample_id: str,
    file_name: str,
    function_name: str,
    fn_start: int,
    fn_end: int,
    cfg: CFG,
    fn_body_root,
    commit_count: int = 0,
    churn: int = 0,
) -> FeatureRow:
    loc = max(0, fn_end - fn_start + 1)

    branch_count = _count_kinds_in_cfg(cfg, {"if"})
    loop_count = _count_kinds_in_cfg(cfg, {"for", "while", "do"})
    cyclomatic = 1 + branch_count + loop_count

    return_count = _count_kinds_in_cfg(cfg, {"return"})
    call_count = _count_kinds_in_cfg(cfg, {"call"})

    max_depth = _max_depth_stmt(fn_body_root, 0)

    bb = len(cfg.blocks)
    ee = len(cfg.edges)
    
    # Read source code
    source_code = _read_source_code(file_name, fn_start, fn_end)
    sensitive_api_calls, high_risk_api_flag = _count_sensitive_from_source(source_code)
    
    # ✅ COMPLETELY REPLACE buggy CFG reachability with our string-based heuristics
    total_unreachable = _count_dead_code_heuristics(source_code)
    un_ratio = float(total_unreachable) / float(bb) if bb > 0 else 0.0

    row = FeatureRow(
        sample_id=sample_id,
        file_name=file_name,
        function_name=function_name,
        loc=loc,
        cyclomatic=cyclomatic,
        branch_count=branch_count,
        loop_count=loop_count,
        max_nesting_depth=max_depth,
        call_count=call_count,
        return_count=return_count,
        basic_blocks=bb,
        cfg_edges=ee,
        unreachable_blocks=total_unreachable,
        unreachable_ratio=un_ratio,
        sensitive_api_calls=sensitive_api_calls,
        high_risk_api_flag=high_risk_api_flag,
        commit_count=commit_count,
        churn=churn,
    )
    return row

def feature_row_to_dict(row: FeatureRow) -> Dict:
    return asdict(row)