import pandas as pd


def label_dataset(input_csv, output_csv):
    df = pd.read_csv(input_csv)

    file_col = df["file_name"].astype(str).str.lower()
    func_col = df["function_name"].astype(str).str.lower()

    # -------------------------
    # DEAD CODE LABEL - IMPROVED
    # -------------------------
    # Include BOTH unreachable blocks AND unused variables/low-usage functions
    df["label_deadcode"] = (
        (df["unreachable_blocks"].fillna(0) >= 2) |
        (df["unreachable_ratio"].fillna(0) >= 0.3) |
        (df["call_count"].fillna(0) == 0)  # Never called = dead code
    ).astype(int)

    # ✅ VULNERABILITY LABEL (from integrated_features)
    # Don't re-label! Just use what integrate_features created
    if "label_vuln" not in df.columns:
        # Fallback if not present
        df["label_vuln"] = (
            (df["sensitive_api_calls"].fillna(0) > 0) |
            (df["cyclomatic"].fillna(0) >= 10)
        ).astype(int)

    df.to_csv(output_csv, index=False)

    print("✅ Saved labeled dataset to:", output_csv)
    print("\nDeadcode distribution:")
    print(df["label_deadcode"].value_counts())

    print("\nVulnerability distribution:")
    print(df["label_vuln"].value_counts())
    
    print(f"\n✅ Total vulnerable functions: {(df['label_vuln'] == 1).sum()}")
    print(f"✅ Total safe functions: {(df['label_vuln'] == 0).sum()}")
    print(f"✅ Total dead code functions: {(df['label_deadcode'] == 1).sum()}")


if __name__ == "__main__":
    label_dataset(
        input_csv="data/intermediate/integrated_features.csv",
        output_csv="data/intermediate/labeled_dataset.csv"
    )