from typing import Dict, Set

from ..cfg.models import CFG

def reachable_blocks(cfg: CFG) -> Set[int]:
    seen: Set[int] = set()
    stack = [cfg.entry]
    while stack:
        u = stack.pop()
        if u in seen:
            continue
        seen.add(u)
        for v in cfg.successors(u):
            if v not in seen:
                stack.append(v)
    return seen

def unreachable_blocks(cfg: CFG) -> Set[int]:
    reach = reachable_blocks(cfg)
    return set(cfg.blocks.keys()) - reach