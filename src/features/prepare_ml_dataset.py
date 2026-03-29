import pandas as pd
from sklearn.preprocessing import StandardScaler


def normalize_features(input_csv, output_csv):
    df = pd.read_csv(input_csv)

    # ⚠️ FIXED: Removed sensitive_api_calls to prevent data leakage
    # We use it for LABELING, not as a FEATURE
    feature_cols = [
        "loc", "cyclomatic", "branch_count", "loop_count",
        "max_nesting_depth", "call_count", "return_count",
        "basic_blocks", "cfg_edges",
        "unreachable_blocks", "unreachable_ratio",
        # "sensitive_api_calls",  ← REMOVED! (prevents leakage)
        # "high_risk_api_flag",   ← REMOVED! (prevents leakage)
        "commit_count", "churn"
    ]

    scaler = StandardScaler()
    df[feature_cols] = scaler.fit_transform(df[feature_cols])

    df.to_csv(output_csv, index=False)
    print("Normalized dataset saved to:", output_csv)
    print(f"Features used: {len(feature_cols)}")
    print(f"Features: {feature_cols}")

if __name__ == "__main__":
    normalize_features(
        input_csv="data/intermediate/labeled_dataset.csv",
        output_csv="data/intermediate/normalized_dataset.csv"
    )