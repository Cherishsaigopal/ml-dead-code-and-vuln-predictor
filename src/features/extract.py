from dataclasses import dataclass, asdict
from typing import Dict, Set

from ..cfg.models import CFG
from ..analysis.reachability import unreachable_blocks
from ..utils.log import get_logger

log = get_logger(__name__)


SENSITIVE_APIS = {
    "strcpy", "strcat", "gets", "sprintf", "vsprintf",
    "memcpy", "scanf", "sscanf", "system", "popen",
}
HIGH_RISK_APIS = {"gets", "strcpy", "sprintf", "vsprintf", "system"}


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


def _walk_stmt_tree(node):
    yield node
    for ch in node.children:
        yield from _walk_stmt_tree(ch)


def _count_sensitive_from_stmt_tree(fn_body_root) -> tuple[int, int]:
    sensitive_api_calls = 0
    high_risk_api_flag = 0

    for node in _walk_stmt_tree(fn_body_root):
        if node.kind != "call":
            continue

        call_name = (node.text or "").strip()
        if call_name in SENSITIVE_APIS:
            sensitive_api_calls += 1
        if call_name in HIGH_RISK_APIS:
            high_risk_api_flag = 1

    return sensitive_api_calls, high_risk_api_flag


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
    un = unreachable_blocks(cfg)
    un_cnt = len(un)
    un_ratio = float(un_cnt) / float(bb) if bb > 0 else 0.0

    sensitive_api_calls, high_risk_api_flag = _count_sensitive_from_stmt_tree(fn_body_root)

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
        unreachable_blocks=un_cnt,
        unreachable_ratio=un_ratio,
        sensitive_api_calls=sensitive_api_calls,
        high_risk_api_flag=high_risk_api_flag,
        commit_count=commit_count,
        churn=churn,
    )
    return row


def feature_row_to_dict(row: FeatureRow) -> Dict:
    return asdict(row)