import pandas as pd
from sklearn.preprocessing import StandardScaler


def normalize_features(input_csv, output_csv):
    df = pd.read_csv(input_csv)

    # ✅ DEAD CODE FEATURES - DO NOT include unreachable metrics!
    # They are dropped during training to prevent leakage
    deadcode_features = [
        "loc", "cyclomatic", "branch_count", "loop_count",
        "max_nesting_depth", "return_count",
        "basic_blocks", "cfg_edges",
        "commit_count", "churn"
        # NOT: unreachable_blocks, unreachable_ratio, call_count (dropped in training)
    ]
    
    # ✅ VULNERABILITY FEATURES - NO sensitive APIs!
    vuln_features = [
        "loc", "cyclomatic", "branch_count", "loop_count",
        "max_nesting_depth", "call_count", "return_count",
        "basic_blocks", "cfg_edges",
        "unreachable_blocks",      # Can use for complexity
        "unreachable_ratio",       # Can use for complexity
        "commit_count", "churn"
        # NOT: sensitive_api_calls, high_risk_api_flag (prevents leakage!)
    ]

    # Normalize all features together
    all_features = list(set(deadcode_features + vuln_features))
    
    scaler = StandardScaler()
    df[all_features] = scaler.fit_transform(df[all_features])

    df.to_csv(output_csv, index=False)
    print("✅ Normalized dataset saved to:", output_csv)
    print(f"Features used: {len(all_features)}")
    print(f"Dead code features: {len(deadcode_features)} (unreachable metrics EXCLUDED)")
    print(f"Vuln features: {len(vuln_features)}")

if __name__ == "__main__":
    normalize_features(
        input_csv="data/intermediate/labeled_dataset.csv",
        output_csv="data/intermediate/normalized_dataset.csv"
    )