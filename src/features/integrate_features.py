import pandas as pd
import json


def norm_path(p: str) -> str:
    return str(p).replace("\\", "/").strip()


def merge_features(features_csv, dead_summary_json, output_csv):
    # Load extracted features
    df = pd.read_csv(features_csv)
    df.columns = df.columns.str.strip()

    # Normalize keys in features.csv
    df["file_name"] = df["file_name"].astype(str).apply(norm_path)
    df["function_name"] = df["function_name"].astype(str).str.strip()

    # Load dead code summary JSON
    with open(dead_summary_json, "r") as f:
        label_data = json.load(f)

    label_df = pd.DataFrame(label_data)
    label_df.columns = label_df.columns.str.strip()

    # Rename JSON columns to match features.csv
    label_df = label_df.rename(columns={
        "file": "file_name",
        "function": "function_name"
    })

    # Normalize keys in JSON
    label_df["file_name"] = label_df["file_name"].astype(str).apply(norm_path)
    label_df["function_name"] = label_df["function_name"].astype(str).str.strip()

    # Create dead code label
    label_df["label_deadcode"] = (
        label_df["dead_block_count"].fillna(0) > 0
    ).astype(int)

    # Merge dead code labels into features
    merged = df.merge(
        label_df[["file_name", "function_name", "label_deadcode", "dead_block_count"]],
        on=["file_name", "function_name"],
        how="left"
    )

    # Fill missing dead code fields
    merged["label_deadcode"] = merged["label_deadcode"].fillna(0).astype(int)
    merged["dead_block_count"] = merged["dead_block_count"].fillna(0).astype(int)

    # Create vulnerability label
    # Rule: if high-risk API exists OR sensitive API calls > 0 => vulnerable
    if "high_risk_api_flag" in merged.columns and "sensitive_api_calls" in merged.columns:
        merged["label_vuln"] = (
            (merged["high_risk_api_flag"].fillna(0) > 0) |
            (merged["sensitive_api_calls"].fillna(0) > 0)
        ).astype(int)
    elif "high_risk_api_flag" in merged.columns:
        merged["label_vuln"] = (merged["high_risk_api_flag"].fillna(0) > 0).astype(int)
    elif "sensitive_api_calls" in merged.columns:
        merged["label_vuln"] = (merged["sensitive_api_calls"].fillna(0) > 0).astype(int)
    else:
        merged["label_vuln"] = 0

    # Save final integrated dataset
    merged.to_csv(output_csv, index=False)
    print("✅ Integrated dataset saved to:", output_csv)


if __name__ == "__main__":
    merge_features(
        features_csv="data/intermediate/features/features.csv",
        dead_summary_json="data/intermediate/features/dead_code_summary.json",
        output_csv="data/intermediate/integrated_features.csv"
    )