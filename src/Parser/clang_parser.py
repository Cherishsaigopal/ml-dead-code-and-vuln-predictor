import os
from pathlib import Path
from typing import List, Optional,Tuple

from clang.cindex import Index, CursorKind, TranslationUnitLoadError
from .models import FunctionInfo, StmtNode, SourceLoc
from ..utils.log import get_logger

log = get_logger(__name__)

def _loc(cursor) -> Optional[SourceLoc]:
    try:
        if cursor.location and cursor.location.file:
            return SourceLoc(
                file=str(cursor.location.file),
                line=int(cursor.location.line),
                col=int(cursor.location.column),
            )
    except Exception:
        pass
    return None

def _spell(cursor) -> str:
    try:
        return cursor.spelling or ""
    except Exception:
        return ""

def _extent_lines(cursor) -> Tuple[int, int]:
    try:
        s = cursor.extent.start.line
        e = cursor.extent.end.line
        return int(s), int(e)
    except Exception:
        return 0, 0

def _is_in_file(cursor, file_path: str) -> bool:
    try:
        return cursor.location.file and str(cursor.location.file) == file_path
    except Exception:
        return False

def _build_stmt_tree(stmt_cursor) -> StmtNode:
    
    k = stmt_cursor.kind

   
    node = StmtNode(kind="stmt", loc=_loc(stmt_cursor), text=k.name)

    if k == CursorKind.COMPOUND_STMT:
        node.kind = "compound"
        for ch in stmt_cursor.get_children():
            node.children.append(_build_stmt_tree(ch))
        return node

    if k == CursorKind.IF_STMT:
        node.kind = "if"
        kids = list(stmt_cursor.get_children())
        
        for ch in kids:
            node.children.append(_build_stmt_tree(ch))
        return node

    if k == CursorKind.FOR_STMT:
        node.kind = "for"
        for ch in stmt_cursor.get_children():
            node.children.append(_build_stmt_tree(ch))
        return node

    if k == CursorKind.WHILE_STMT:
        node.kind = "while"
        for ch in stmt_cursor.get_children():
            node.children.append(_build_stmt_tree(ch))
        return node

    if k == CursorKind.DO_STMT:
        node.kind = "do"
        for ch in stmt_cursor.get_children():
            node.children.append(_build_stmt_tree(ch))
        return node

    if k == CursorKind.RETURN_STMT:
        node.kind = "return"
        return node

    if k == CursorKind.BREAK_STMT:
        node.kind = "break"
        return node

    if k == CursorKind.CONTINUE_STMT:
        node.kind = "continue"
        return node

    if k == CursorKind.CALL_EXPR:
        node.kind = "call"
        node.text = _spell(stmt_cursor)
        return node

    
    for ch in stmt_cursor.get_children():
        node.children.append(_build_stmt_tree(ch))
    return node

class ClangFunctionExtractor:
    def __init__(self, clang_args: Optional[List[str]] = None):
        self.clang_args = clang_args or ["-std=c++17"]

        
        if "LIBCLANG_PATH" in os.environ:
            log.info("LIBCLANG_PATH set to %s", os.environ["LIBCLANG_PATH"])

    def parse_file(self, file_path: Path) -> List[FunctionInfo]:
        file_path = file_path.resolve()
        idx = Index.create()

        try:
            tu = idx.parse(
                str(file_path),
                args=self.clang_args,
                options=0,
            )
        except TranslationUnitLoadError as e:
            log.error("Failed parsing %s: %s", file_path, e)
            return []

        funcs: List[FunctionInfo] = []
        file_str = str(file_path)

        for c in tu.cursor.get_children():
            if c.kind == CursorKind.FUNCTION_DECL and _is_in_file(c, file_str):
                
                body = None
                for ch in c.get_children():
                    if ch.kind == CursorKind.COMPOUND_STMT:
                        body = _build_stmt_tree(ch)
                        break
                if body is None:
                    continue

                s, e = _extent_lines(c)
                funcs.append(
                    FunctionInfo(
                        file=file_str,
                        name=_spell(c),
                        start_line=s,
                        end_line=e,
                        body=body,
                    )
                )

        return funcs