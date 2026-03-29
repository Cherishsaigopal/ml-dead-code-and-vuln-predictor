import pandas as pd
from sklearn.preprocessing import StandardScaler


def normalize_features(input_csv, output_csv):
    df = pd.read_csv(input_csv)

    # ✅ DEADCODE FEATURES (includes unreachable for dead code detection)
    deadcode_features = [
        "loc", "cyclomatic", "branch_count", "loop_count",
        "max_nesting_depth", "call_count", "return_count",
        "basic_blocks", "cfg_edges",
        "unreachable_blocks",      # ✅ MUST INCLUDE for dead code training
        "unreachable_ratio",       # ✅ MUST INCLUDE for dead code training
        "commit_count", "churn"
    ]
    
    # ✅ VULNERABILITY FEATURES (NO sensitive_api_calls to prevent leakage)
    vuln_features = [
        "loc", "cyclomatic", "branch_count", "loop_count",
        "max_nesting_depth", "call_count", "return_count",
        "basic_blocks", "cfg_edges",
        "unreachable_blocks",      # Can use for complexity
        "unreachable_ratio",       # Can use for complexity
        "commit_count", "churn"
        # NOT: sensitive_api_calls (prevents leakage!)
    ]

    # Normalize all features together
    all_features = list(set(deadcode_features + vuln_features))
    
    scaler = StandardScaler()
    df[all_features] = scaler.fit_transform(df[all_features])

    df.to_csv(output_csv, index=False)
    print("✅ Normalized dataset saved to:", output_csv)
    print(f"Features used: {len(all_features)}")
    print(f"Includes unreachable metrics: YES (for dead code training)")

if __name__ == "__main__":
    normalize_features(
        input_csv="data/intermediate/labeled_dataset.csv",
        output_csv="data/intermediate/normalized_dataset.csv"
    )