from dataclasses import dataclass
from typing import List, Optional

@dataclass(frozen=True)
class SourceLoc:
    file: str
    line: int
    col: int

@dataclass
class StmtNode:
    
    kind: str
    loc: Optional[SourceLoc]
    text: str = ""
    children: List["StmtNode"] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []

@dataclass
class FunctionInfo:
    file: str
    name: str
    start_line: int
    end_line: int
    body: StmtNode  