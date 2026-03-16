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
    df["label_vuln"] = 0

    # Juliet dataset rules
    juliet = file_col.str.contains("juliet-test-suite-c", na=False)

    df.loc[juliet & func_col.str.contains("bad", na=False), "label_vuln"] = 1
    df.loc[juliet & func_col.str.contains("good", na=False), "label_vuln"] = 0

    # Non-Juliet heuristic
    non_juliet = ~juliet

    df.loc[
        non_juliet & (
            (df["sensitive_api_calls"] > 0) |
            (df["cyclomatic"] >= 10)
        ),
        "label_vuln"
    ] = 1

    df.to_csv(output_csv, index=False)

    print("Saved labeled dataset to:", output_csv)
    print("\nDeadcode distribution:")
    print(df["label_deadcode"].value_counts())

    print("\nVulnerability distribution:")
    print(df["label_vuln"].value_counts())


if __name__ == "__main__":
    label_dataset(
        input_csv="data/intermediate/integrated_features.csv",
        output_csv="data/intermediate/labeled_dataset.csv"
    )