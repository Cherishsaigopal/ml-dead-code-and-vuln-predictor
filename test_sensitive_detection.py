from pathlib import Path
from src.Parser.clang_parser import ClangFunctionExtractor
from src.cfg.builder import build_cfg
from src.features.extract import extract_features_from_cfg, feature_row_to_dict

# Parse test.cpp
extractor = ClangFunctionExtractor()
functions = extractor.parse_file(Path("test.cpp"))

print("Testing Sensitive API Detection\n")
print("=" * 80)

for fn in functions:
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
        
        print(f"\nFunction: {fn.name}")
        print(f"  sensitive_api_calls: {row['sensitive_api_calls']}")
        print(f"  high_risk_api_flag: {row['high_risk_api_flag']}")
        
        # Expected values
        if fn.name == "test1":
            assert row['sensitive_api_calls'] == 0, "test1 should have 0 sensitive calls"
            print("  ✓ CORRECT (0 calls expected)")
        elif fn.name == "test3":
            assert row['sensitive_api_calls'] > 0, "test3 should detect strcpy!"
            print(f"  ✓ CORRECT ({row['sensitive_api_calls']} strcpy call detected)")
        elif fn.name == "test5":
            assert row['sensitive_api_calls'] > 0, "test5 should detect strcpy!"
            print(f"  ✓ CORRECT ({row['sensitive_api_calls']} strcpy call detected)")
            
    except AssertionError as e:
        print(f"  ❌ ERROR: {e}")
    except Exception as e:
        print(f"  ❌ Exception: {e}")

print("\n" + "=" * 80)