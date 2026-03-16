import os
from pathlib import Path
from typing import List, Optional, Tuple

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
        return cursor.spelling or cursor.displayname or ""
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


def _function_kinds():
    return {
        CursorKind.FUNCTION_DECL,
        CursorKind.CXX_METHOD,
        CursorKind.CONSTRUCTOR,
        CursorKind.DESTRUCTOR,
        CursorKind.CONVERSION_FUNCTION,
    }


def _walk(cursor):
    yield cursor
    for ch in cursor.get_children():
        yield from _walk(ch)


def _find_first_call_name(cursor) -> str:
    try:
        for ch in cursor.get_children():
            if ch.kind == CursorKind.CALL_EXPR:
                name = _spell(ch)
                if name:
                    return name
            nested = _find_first_call_name(ch)
            if nested:
                return nested
    except Exception:
        pass
    return ""


def _build_stmt_tree(stmt_cursor, depth: int = 0, max_depth: int = 40) -> StmtNode:
    if depth > max_depth:
        return StmtNode(kind="stmt", loc=_loc(stmt_cursor), text="MAX_DEPTH")

    k = stmt_cursor.kind
    node = StmtNode(kind="stmt", loc=_loc(stmt_cursor), text=k.name)

    # Only preserve control-flow / structural statements.
    if k == CursorKind.COMPOUND_STMT:
        node.kind = "compound"
        for ch in stmt_cursor.get_children():
            node.children.append(_build_stmt_tree(ch, depth + 1, max_depth))
        return node

    if k == CursorKind.IF_STMT:
        node.kind = "if"
        for ch in stmt_cursor.get_children():
            if ch.kind in {
                CursorKind.COMPOUND_STMT,
                CursorKind.IF_STMT,
                CursorKind.FOR_STMT,
                CursorKind.WHILE_STMT,
                CursorKind.DO_STMT,
                CursorKind.SWITCH_STMT,
                CursorKind.CASE_STMT,
                CursorKind.DEFAULT_STMT,
                CursorKind.RETURN_STMT,
                CursorKind.BREAK_STMT,
                CursorKind.CONTINUE_STMT,
                CursorKind.CALL_EXPR,
                CursorKind.DECL_STMT,
                CursorKind.BINARY_OPERATOR,
                CursorKind.UNARY_OPERATOR,
            }:
                node.children.append(_build_stmt_tree(ch, depth + 1, max_depth))
        return node

    if k == CursorKind.FOR_STMT:
        node.kind = "for"
        for ch in stmt_cursor.get_children():
            if ch.kind in {
                CursorKind.COMPOUND_STMT,
                CursorKind.IF_STMT,
                CursorKind.FOR_STMT,
                CursorKind.WHILE_STMT,
                CursorKind.DO_STMT,
                CursorKind.SWITCH_STMT,
                CursorKind.CASE_STMT,
                CursorKind.DEFAULT_STMT,
                CursorKind.RETURN_STMT,
                CursorKind.BREAK_STMT,
                CursorKind.CONTINUE_STMT,
                CursorKind.CALL_EXPR,
                CursorKind.DECL_STMT,
                CursorKind.BINARY_OPERATOR,
                CursorKind.UNARY_OPERATOR,
            }:
                node.children.append(_build_stmt_tree(ch, depth + 1, max_depth))
        return node

    if k == CursorKind.WHILE_STMT:
        node.kind = "while"
        for ch in stmt_cursor.get_children():
            if ch.kind in {
                CursorKind.COMPOUND_STMT,
                CursorKind.IF_STMT,
                CursorKind.FOR_STMT,
                CursorKind.WHILE_STMT,
                CursorKind.DO_STMT,
                CursorKind.SWITCH_STMT,
                CursorKind.CASE_STMT,
                CursorKind.DEFAULT_STMT,
                CursorKind.RETURN_STMT,
                CursorKind.BREAK_STMT,
                CursorKind.CONTINUE_STMT,
                CursorKind.CALL_EXPR,
                CursorKind.DECL_STMT,
                CursorKind.BINARY_OPERATOR,
                CursorKind.UNARY_OPERATOR,
            }:
                node.children.append(_build_stmt_tree(ch, depth + 1, max_depth))
        return node

    if k == CursorKind.DO_STMT:
        node.kind = "do"
        for ch in stmt_cursor.get_children():
            if ch.kind in {
                CursorKind.COMPOUND_STMT,
                CursorKind.IF_STMT,
                CursorKind.FOR_STMT,
                CursorKind.WHILE_STMT,
                CursorKind.DO_STMT,
                CursorKind.SWITCH_STMT,
                CursorKind.CASE_STMT,
                CursorKind.DEFAULT_STMT,
                CursorKind.RETURN_STMT,
                CursorKind.BREAK_STMT,
                CursorKind.CONTINUE_STMT,
                CursorKind.CALL_EXPR,
                CursorKind.DECL_STMT,
                CursorKind.BINARY_OPERATOR,
                CursorKind.UNARY_OPERATOR,
            }:
                node.children.append(_build_stmt_tree(ch, depth + 1, max_depth))
        return node

    if k == CursorKind.SWITCH_STMT:
        node.kind = "switch"
        for ch in stmt_cursor.get_children():
            if ch.kind in {
                CursorKind.COMPOUND_STMT,
                CursorKind.CASE_STMT,
                CursorKind.DEFAULT_STMT,
                CursorKind.BREAK_STMT,
                CursorKind.RETURN_STMT,
                CursorKind.CALL_EXPR,
            }:
                node.children.append(_build_stmt_tree(ch, depth + 1, max_depth))
        return node

    if k == CursorKind.CASE_STMT:
        node.kind = "case"
        for ch in stmt_cursor.get_children():
            if ch.kind in {
                CursorKind.COMPOUND_STMT,
                CursorKind.IF_STMT,
                CursorKind.FOR_STMT,
                CursorKind.WHILE_STMT,
                CursorKind.DO_STMT,
                CursorKind.SWITCH_STMT,
                CursorKind.CASE_STMT,
                CursorKind.DEFAULT_STMT,
                CursorKind.RETURN_STMT,
                CursorKind.BREAK_STMT,
                CursorKind.CONTINUE_STMT,
                CursorKind.CALL_EXPR,
            }:
                node.children.append(_build_stmt_tree(ch, depth + 1, max_depth))
        return node

    if k == CursorKind.DEFAULT_STMT:
        node.kind = "default"
        for ch in stmt_cursor.get_children():
            if ch.kind in {
                CursorKind.COMPOUND_STMT,
                CursorKind.IF_STMT,
                CursorKind.FOR_STMT,
                CursorKind.WHILE_STMT,
                CursorKind.DO_STMT,
                CursorKind.SWITCH_STMT,
                CursorKind.CASE_STMT,
                CursorKind.DEFAULT_STMT,
                CursorKind.RETURN_STMT,
                CursorKind.BREAK_STMT,
                CursorKind.CONTINUE_STMT,
                CursorKind.CALL_EXPR,
            }:
                node.children.append(_build_stmt_tree(ch, depth + 1, max_depth))
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
        node.text = _spell(stmt_cursor) or "call"
        return node

    if k == CursorKind.DECL_STMT:
        node.kind = "decl"
        return node

    # For all expression-heavy nodes, do not recurse deeply.
    if k in {
        CursorKind.BINARY_OPERATOR,
        CursorKind.UNARY_OPERATOR,
        CursorKind.CONDITIONAL_OPERATOR,
        CursorKind.DECL_REF_EXPR,
        CursorKind.MEMBER_REF_EXPR,
        CursorKind.INTEGER_LITERAL,
        CursorKind.FLOATING_LITERAL,
        CursorKind.STRING_LITERAL,
        CursorKind.CXX_BOOL_LITERAL_EXPR,
        CursorKind.PAREN_EXPR,
        CursorKind.INIT_LIST_EXPR,
        CursorKind.CSTYLE_CAST_EXPR,
        CursorKind.CXX_STATIC_CAST_EXPR,
        CursorKind.CXX_FUNCTIONAL_CAST_EXPR,
        CursorKind.UNEXPOSED_EXPR,
    }:
        call_name = _find_first_call_name(stmt_cursor)
        if call_name:
            node.kind = "call"
            node.text = call_name
        else:
            node.kind = "stmt"
        return node

    # Fallback: keep it shallow.
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
        except Exception as e:
            log.error("Unexpected parse failure for %s: %s", file_path, e)
            return []

        funcs: List[FunctionInfo] = []
        file_str = str(file_path)

        for c in _walk(tu.cursor):
            if c.kind not in _function_kinds():
                continue

            if not _is_in_file(c, file_str):
                continue

            body = None
            for ch in c.get_children():
                if ch.kind == CursorKind.COMPOUND_STMT:
                    body = _build_stmt_tree(ch)
                    break

            if body is None:
                continue

            s, e = _extent_lines(c)
            name = _spell(c)

            if not name:
                try:
                    name = c.displayname or c.spelling or c.kind.name
                except Exception:
                    name = c.kind.name

            funcs.append(
                FunctionInfo(
                    file=file_str,
                    name=name,
                    start_line=s,
                    end_line=e,
                    body=body,
                )
            )

        return funcs