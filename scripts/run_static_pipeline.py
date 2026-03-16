import csv
from pathlib import Path
import hashlib
from collections import defaultdict

from src.utils.fs import ensure_dir, list_source_files, relpath
from src.utils.jsonio import write_json
from src.utils.log import get_logger

from src.Parser.clang_parser import ClangFunctionExtractor
from src.cfg.builder import build_cfg
from src.analysis.reachability import reachable_blocks, unreachable_blocks
from src.analysis.dead_code import detect_dead_code
from src.features.extract import extract_features_from_cfg, feature_row_to_dict

log = get_logger("week7")


MAX_FILES = 800


def _sample_id(file_name: str, func_name: str, start: int, end: int) -> str:
    s = f"{file_name}:{func_name}:{start}:{end}"
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def keep_only_selected_juliet_cwes(path: Path) -> bool:
    p = str(path).lower().replace("\\", "/")

    if "juliet-test-suite-c" not in p:
        return True

    allowed_cwes = [
        "cwe134_uncontrolled_format_string",
        "cwe190_integer_overflow",
    ]

    if not any(cwe in p for cwe in allowed_cwes):
        return False

    # Keep only simpler Juliet variants
    skip_suffix_patterns = [
        "_81", "_82", "_83", "_84",
        "_53", "_54", "_61", "_62", "_63", "_64", "_65",
    ]

    stem = path.stem.lower()
    return not any(pattern in stem for pattern in skip_suffix_patterns)


def should_skip_file(path: Path) -> bool:
    p = str(path).lower().replace("\\", "/")

    # Skip C-Plus-Plus completely
    if "/c-plus-plus/" in p:
        return True

    # Keep only a tiny subset of imgui
    if "/imgui/" in p:
        allowed_imgui_files = {
            "imgui.cpp",
            "imgui_draw.cpp",
        }
        return path.name.lower() not in allowed_imgui_files

    # Juliet-specific filtering
    if "juliet-test-suite-c" not in p:
        return False

    if "testcasesupport" in p:
        return True

    skip_keywords = [
        "w32",
        "socket",
        "thread",
        "console",
        "environment",
        "connect",
        "winsock",
        "std_thread",
        "fgets",
        "fscanf",
        "rand",
        "recv",
        "listen",
        "accept",
    ]

    return any(k in p for k in skip_keywords)


def repo_name_from_path(path: Path, repo_root: Path) -> str:
    rel = path.relative_to(repo_root)
    return rel.parts[0] if rel.parts else "UNKNOWN"


def build_extractor_for_file(file_path: Path, repo_root: Path):
    repo_name = repo_name_from_path(file_path, repo_root)
    ext = file_path.suffix.lower()

    includes = [f"-I{repo_root}"]

    if repo_name == "juliet-test-suite-c":
        juliet_support = repo_root / "juliet-test-suite-c" / "testcasesupport"
        if juliet_support.exists():
            includes.append(f"-I{juliet_support}")

    elif repo_name == "imgui":
        imgui_root = repo_root / "imgui"
        includes.extend([
            f"-I{imgui_root}",
            f"-I{imgui_root / 'backends'}",
            f"-I{imgui_root / 'misc'}",
        ])

    if ext == ".c":
        return ClangFunctionExtractor(
            clang_args=["-x", "c", "-std=c11", *includes]
        )

    if ext in {".cpp", ".cc", ".cxx"}:
        return ClangFunctionExtractor(
            clang_args=["-x", "c++", "-std=c++17", *includes]
        )

    return None


def main():
    repo_root = Path("data/raw/repos").resolve()
    out_root = Path("data/intermediate").resolve()
    out_feat = out_root / "features"

    ensure_dir(out_feat)

    sources = list_source_files(repo_root)

    filtered_sources = []
    skipped_count = 0

    for f in sources:
        if not keep_only_selected_juliet_cwes(f):
            skipped_count += 1
            continue
        if should_skip_file(f):
            skipped_count += 1
            continue
        filtered_sources.append(f)

    filtered_sources = filtered_sources[:MAX_FILES]

    log.info("Found %d source files under %s", len(sources), repo_root)
    log.info("Using %d source files after filtering", len(filtered_sources))
    log.info("Skipped %d files", skipped_count)

    discovered_by_repo = defaultdict(int)
    parsed_ok_by_repo = defaultdict(int)
    parse_fail_by_repo = defaultdict(int)
    functions_by_repo = defaultdict(int)
    feature_rows_by_repo = defaultdict(int)

    for f in filtered_sources:
        discovered_by_repo[repo_name_from_path(f, repo_root)] += 1

    feature_rows = []
    dead_rows = []

    parsed_files = 0
    failed_files = 0

    for f in filtered_sources:
        repo_name = repo_name_from_path(f, repo_root)

        extractor = build_extractor_for_file(f, repo_root)
        if extractor is None:
            continue

        try:
            funcs = extractor.parse_file(f)
            parsed_files += 1
            parsed_ok_by_repo[repo_name] += 1
        except Exception as e:
            failed_files += 1
            parse_fail_by_repo[repo_name] += 1
            log.error("Failed parsing %s: %s", f, e)
            continue

        if not funcs:
            log.warning("No functions extracted from %s", f)
            continue

        functions_by_repo[repo_name] += len(funcs)

        for fn in funcs:
            try:
                cfg = build_cfg(fn)

                sid = _sample_id(fn.file, fn.name, fn.start_line, fn.end_line)
                file_rel = relpath(Path(fn.file), repo_root)

                # Compute reachability in memory only
                _ = reachable_blocks(cfg)
                _ = unreachable_blocks(cfg)

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
                feature_rows_by_repo[repo_name] += 1

            except Exception as e:
                log.error("Failed processing function %s in %s: %s", fn.name, f, e)
                continue

    csv_path = out_feat / "features.csv"
    if feature_rows:
        keys = list(feature_rows[0].keys())
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for row in feature_rows:
                writer.writerow(row)

    write_json(out_feat / "dead_code_summary.json", dead_rows)

    log.info("Done.")
    log.info("Parsed files successfully: %d", parsed_files)
    log.info("Files failed to parse: %d", failed_files)
    log.info("Feature rows written: %d", len(feature_rows))
    log.info("Features CSV: %s", csv_path)

    log.info("----- Repo-wise summary -----")
    all_repos = sorted(
        set(discovered_by_repo)
        | set(parsed_ok_by_repo)
        | set(parse_fail_by_repo)
        | set(functions_by_repo)
        | set(feature_rows_by_repo)
    )
    for repo in all_repos:
        log.info(
            "[%s] discovered=%d parsed_ok=%d parse_fail=%d functions=%d feature_rows=%d",
            repo,
            discovered_by_repo.get(repo, 0),
            parsed_ok_by_repo.get(repo, 0),
            parse_fail_by_repo.get(repo, 0),
            functions_by_repo.get(repo, 0),
            feature_rows_by_repo.get(repo, 0),
        )


if __name__ == "__main__":
    main()