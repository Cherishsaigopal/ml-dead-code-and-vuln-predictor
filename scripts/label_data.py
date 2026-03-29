import pandas as pd


def label_dataset(input_csv, output_csv):
    df = pd.read_csv(input_csv)

    file_col = df["file_name"].astype(str).str.lower()
    func_col = df["function_name"].astype(str).str.lower()

    # -------------------------
    # DEAD CODE LABEL
    # -------------------------
    # Stricter rule to avoid overly easy / noisy labels
    df["label_deadcode"] = (
        (df["unreachable_blocks"] >= 2) |
        (df["unreachable_ratio"] >= 0.3)
    ).astype(int)

    # -------------------------
    # VULNERABILITY LABEL
    # -------------------------
    # FIXED: Use consistent rule for ALL datasets
    # Label as vulnerable if: has risky APIs OR complex code
    df["label_vuln"] = (
        (df["sensitive_api_calls"].fillna(0) > 0) |  # strcpy, gets, sprintf, etc.
        (df["cyclomatic"].fillna(0) >= 10)  # High complexity
    ).astype(int)

    df.to_csv(output_csv, index=False)

    print("Saved labeled dataset to:", output_csv)
    print("\nDeadcode distribution:")
    print(df["label_deadcode"].value_counts())

    print("\nVulnerability distribution:")
    print(df["label_vuln"].value_counts())
    
    print(f"\n✅ Total vulnerable functions: {(df['label_vuln'] == 1).sum()}")
    print(f"✅ Total safe functions: {(df['label_vuln'] == 0).sum()}")


if __name__ == "__main__":
    label_dataset(
        input_csv="data/intermediate/integrated_features.csv",
        output_csv="data/intermediate/labeled_dataset.csv"
    )