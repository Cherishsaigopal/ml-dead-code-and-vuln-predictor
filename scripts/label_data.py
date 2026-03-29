import pandas as pd


def label_dataset(input_csv, output_csv):
    df = pd.read_csv(input_csv)

    # ✅ DEAD CODE LABEL - Use ONLY unreachable blocks from integrate_features
    # Don't re-label - just keep what integrate_features already labeled
    # (integrate_features.py already created label_deadcode based on dead_block_count)
    
    if "label_deadcode" not in df.columns:
        # Fallback: if not present, use conservative rule
        df["label_deadcode"] = 0  # Default: assume no dead code
    
    # ✅ VULNERABILITY LABEL  
    if "label_vuln" not in df.columns:
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