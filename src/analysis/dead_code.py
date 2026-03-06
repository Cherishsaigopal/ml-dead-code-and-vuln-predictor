from dataclasses import dataclass
from typing import List, Set, Tuple

from ..cfg.models import CFG
from .reachability import unreachable_blocks

@dataclass
class DeadCodeFinding:
    block_id: int
    reason: str
    lines: List[int]

def detect_dead_code(cfg: CFG) -> List[DeadCodeFinding]:
    
    dead: List[DeadCodeFinding] = []
    un = unreachable_blocks(cfg)

    for bid in sorted(un):
        b = cfg.blocks[bid]
        lines = [ln for ln in b.stmt_lines if ln != -1]
        dead.append(
            DeadCodeFinding(
                block_id=bid,
                reason="unreachable_block",
                lines=sorted(set(lines)),
            )
        )

    return dead