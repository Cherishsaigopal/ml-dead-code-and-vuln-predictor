import csv
from pathlib import Path
import hashlib

from src.utils.fs import ensure_dir, list_source_files, relpath
from src.utils.jsonio import write_json
from src.utils.log import get_logger

from src.Parser.clang_parser import ClangFunctionExtractor
from src.cfg.builder import build_cfg
from src.analysis.reachability import reachable_blocks, unreachable_blocks
from src.analysis.dead_code import detect_dead_code
from src.features.extract import extract_features_from_cfg, feature_row_to_dict

log = get_logger("week7")

def _sample_id(file_name: str, func_name: str, start: int, end: int) -> str:
    s = f"{file_name}:{func_name}:{start}:{end}"
    return hashlib.md5(s.encode("utf-8")).hexdigest()

def main():
    repo_root = Path("data/raw/repos").resolve() 
    out_root = Path("data/intermediate").resolve()

    out_cfg = out_root / "cfg"
    out_reach = out_root / "reachability"
    out_feat = out_root / "features"
    ensure_dir(out_cfg)
    ensure_dir(out_reach)
    ensure_dir(out_feat)

    
    extractor = ClangFunctionExtractor(clang_args=["-std=c++17", f"-I{repo_root}"])

    sources = list_source_files(repo_root)
    log.info("Found %d source files under %s", len(sources), repo_root)

    feature_rows = []
    dead_rows = []

    for f in sources:
        funcs = extractor.parse_file(f)
        if not funcs:
            continue

        for fn in funcs:
            cfg = build_cfg(fn)

            sid = _sample_id(fn.file, fn.name, fn.start_line, fn.end_line)
            file_rel = relpath(Path(fn.file), repo_root)

            
            cfg_obj = {
                "sample_id": sid,
                "file": file_rel,
                "function": fn.name,
                "entry": cfg.entry,
                "exit": cfg.exit,
                "blocks": {
                    str(bid): {
                        "stmt_kinds": cfg.blocks[bid].stmt_kinds,
                        "stmt_lines": cfg.blocks[bid].stmt_lines,
                    }
                    for bid in cfg.blocks
                },
                "edges": [[a, b] for (a, b) in sorted(cfg.edges)],
            }
            write_json(out_cfg / f"{sid}.json", cfg_obj)

            
            reach = reachable_blocks(cfg)
            un = unreachable_blocks(cfg)
            reach_obj = {
                "sample_id": sid,
                "file": file_rel,
                "function": fn.name,
                "reachable_blocks": sorted(list(reach)),
                "unreachable_blocks": sorted(list(un)),
            }
            write_json(out_reach / f"{sid}.json", reach_obj)

           
            dead = detect_dead_code(cfg)
            dead_rows.append({
                "sample_id": sid,
                "file": file_rel,
                "function": fn.name,
                "dead_block_count": len(dead),
                "dead_lines": sorted({ln for d in dead for ln in d.lines}),
            })

            
            row = extract_features_from_cfg(
                sample_id=sid,
                file_name=file_rel,
                function_name=fn.name,
                fn_start=fn.start_line,
                fn_end=fn.end_line,
                cfg=cfg,
                fn_body_root=fn.body,
                commit_count=0,
                churn=0,
            )
            feature_rows.append(feature_row_to_dict(row))

    
    csv_path = out_feat / "features.csv"
    if feature_rows:
        keys = list(feature_rows[0].keys())
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            for r in feature_rows:
                w.writerow(r)

    
    write_json(out_feat / "dead_code_summary.json", dead_rows)

    log.info("Done.")
    log.info("CFG dumps: %s", out_cfg)
    log.info("Reachability: %s", out_reach)
    log.info("Features CSV: %s", csv_path)

if __name__ == "__main__":
    main()