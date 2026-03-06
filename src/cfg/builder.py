from dataclasses import dataclass
from typing import List, Optional, Tuple

from .models import CFG, BasicBlock
from ..Parser.models import FunctionInfo, StmtNode
from ..utils.log import get_logger

log = get_logger(__name__)

@dataclass
class _BuildState:
    next_id: int

def _new_block(state: _BuildState) -> BasicBlock:
    b = BasicBlock(id=state.next_id)
    state.next_id += 1
    return b

def _line_of(node: StmtNode) -> int:
    return int(node.loc.line) if node.loc is not None else -1

def _add_stmt(block: BasicBlock, node: StmtNode) -> None:
    block.stmt_kinds.append(node.kind)
    block.stmt_lines.append(_line_of(node))

def build_cfg(fn: FunctionInfo) -> CFG:
    
    st = _BuildState(next_id=0)
    blocks = {}
    edges = set()

    entry = _new_block(st)
    blocks[entry.id] = entry

    exitb = _new_block(st)
    blocks[exitb.id] = exitb

    
    start_block, end_blocks = _build_stmt_list(st, blocks, edges, entry, fn.body.children, loop_ctx=None)

   
    for eb in end_blocks:
        edges.add((eb, exitb.id))

    return CFG(
        func_name=fn.name,
        file=fn.file,
        entry=entry.id,
        exit=exitb.id,
        blocks=blocks,
        edges=edges,
    )

@dataclass
class _LoopCtx:
    cond_block: int
    after_block: int

def _build_stmt_list(
    st: _BuildState,
    blocks: dict,
    edges: set,
    cur_block: BasicBlock,
    stmts: List[StmtNode],
    loop_ctx: Optional[_LoopCtx],
) -> Tuple[BasicBlock, List[int]]:
    
    open_ends = [cur_block.id]

    for node in stmts:
        
        if len(open_ends) > 1:
            join = _new_block(st)
            blocks[join.id] = join
            for e in open_ends:
                edges.add((e, join.id))
            cur_block = join
            open_ends = [cur_block.id]
        else:
            
            cur_block = blocks[open_ends[0]]

        
        k = node.kind

        if k == "compound":
            cur_block, open_ends = _build_stmt_list(st, blocks, edges, cur_block, node.children, loop_ctx)
            continue

        if k == "if":
            _add_stmt(cur_block, node)

            then_block = _new_block(st)
            blocks[then_block.id] = then_block

            else_block = _new_block(st)
            blocks[else_block.id] = else_block

            after_if = _new_block(st)
            blocks[after_if.id] = after_if

            
            edges.add((cur_block.id, then_block.id))
            edges.add((cur_block.id, else_block.id))

            
            kids = node.children

            then_body = kids[1] if len(kids) >= 2 else None
            else_body = kids[2] if len(kids) >= 3 else None

            then_ends = [then_block.id]
            if then_body is not None:
                _, then_ends = _build_stmt_list(st, blocks, edges, then_block,
                                               then_body.children if then_body.kind == "compound" else [then_body],
                                               loop_ctx)

            else_ends = [else_block.id]
            if else_body is not None:
                _, else_ends = _build_stmt_list(st, blocks, edges, else_block,
                                               else_body.children if else_body.kind == "compound" else [else_body],
                                               loop_ctx)

          
            for e in then_ends:
                edges.add((e, after_if.id))
            for e in else_ends:
                edges.add((e, after_if.id))

            cur_block = after_if
            open_ends = [cur_block.id]
            continue

        if k in ("for", "while", "do"):
            _add_stmt(cur_block, node)

            cond = _new_block(st)
            blocks[cond.id] = cond

            body = _new_block(st)
            blocks[body.id] = body

            after = _new_block(st)
            blocks[after.id] = after

           
            edges.add((cur_block.id, cond.id))
            
            edges.add((cond.id, body.id))
            edges.add((cond.id, after.id))

            
            body_node = node.children[-1] if node.children else None
            loop_ctx2 = _LoopCtx(cond_block=cond.id, after_block=after.id)

            body_ends = [body.id]
            if body_node is not None:
                _, body_ends = _build_stmt_list(st, blocks, edges, body,
                                               body_node.children if body_node.kind == "compound" else [body_node],
                                               loop_ctx2)

            
            for e in body_ends:
                edges.add((e, cond.id))

            
            cur_block = after
            open_ends = [cur_block.id]
            continue

        if k == "return":
            _add_stmt(cur_block, node)
            
            open_ends = []
            
            newb = _new_block(st)
            blocks[newb.id] = newb
            cur_block = newb
            open_ends = [cur_block.id]  
            continue

        if k == "break":
            _add_stmt(cur_block, node)
            if loop_ctx is not None:
                edges.add((cur_block.id, loop_ctx.after_block))
            open_ends = []
            newb = _new_block(st)
            blocks[newb.id] = newb
            cur_block = newb
            open_ends = [cur_block.id]  
            continue

        if k == "continue":
            _add_stmt(cur_block, node)
            if loop_ctx is not None:
                edges.add((cur_block.id, loop_ctx.cond_block))
            open_ends = []
            newb = _new_block(st)
            blocks[newb.id] = newb
            cur_block = newb
            open_ends = [cur_block.id]
            continue

        
        _add_stmt(cur_block, node)

       
        for ch in node.children:
            if ch.kind == "call":
                _add_stmt(cur_block, ch)

    return cur_block, open_ends