from pathlib import Path
from src.Parser.clang_parser import ClangFunctionExtractor
from src.cfg.builder import build_cfg
from src.features.extract import extract_features_from_cfg, feature_row_to_dict

# Parse test.cpp
extractor = ClangFunctionExtractor()
functions = extractor.parse_file(Path("test.cpp"))

print(f"✓ Found {len(functions)} functions\n")

for fn in functions:
    print(f"Function: {fn.name}")
    print(f"  Lines: {fn.start_line}-{fn.end_line}")
    
    try:
        cfg = build_cfg(fn)
        feature_row = extract_features_from_cfg(
            sample_id="test",
            file_name=fn.file,
            function_name=fn.name,
            fn_start=fn.start_line,
            fn_end=fn.end_line,
            cfg=cfg,
            fn_body_root=fn.body,
            commit_count=0,
            churn=0,
        )
        
        row = feature_row_to_dict(feature_row)
        print(f"  Features extracted: {len(row)} features")
        print(f"    - cyclomatic: {row.get('cyclomatic', 'N/A')}")
        print(f"    - sensitive_api_calls: {row.get('sensitive_api_calls', 'N/A')}")
        print(f"    - unreachable_blocks: {row.get('unreachable_blocks', 'N/A')}")
        print(f"    - loc: {row.get('loc', 'N/A')}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    print()