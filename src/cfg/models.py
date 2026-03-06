from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

@dataclass
class BasicBlock:
    id: int
    stmt_kinds: List[str] = field(default_factory=list)
    stmt_lines: List[int] = field(default_factory=list)

@dataclass
class CFG:
    func_name: str
    file: str
    entry: int
    exit: int
    blocks: Dict[int, BasicBlock]
    edges: Set[Tuple[int, int]]  

    def successors(self, u: int) -> List[int]:
        out = []
        for a, b in self.edges:
            if a == u:
                out.append(b)
        return out