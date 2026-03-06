import pandas as pd
from sklearn.preprocessing import StandardScaler


def normalize_features(input_csv, output_csv):
    df = pd.read_csv(input_csv)

    feature_cols = [
        "loc", "cyclomatic", "branch_count", "loop_count",
        "max_nesting_depth", "call_count", "return_count",
        "basic_blocks", "cfg_edges",
        "unreachable_blocks", "unreachable_ratio",
        "sensitive_api_calls",
        "commit_count", "churn"
    ]

    scaler = StandardScaler()
    df[feature_cols] = scaler.fit_transform(df[feature_cols])

    df.to_csv(output_csv, index=False)
    print("Normalized dataset saved to:", output_csv)
if __name__ == "__main__":
    normalize_features(
        input_csv="data/intermediate/integrated_features.csv",
        output_csv="data/intermediate/normalized_dataset.csv"
    )