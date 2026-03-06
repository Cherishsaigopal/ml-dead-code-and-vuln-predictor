import pandas as pd


def compute_correlation(input_csv, output_csv):
    df = pd.read_csv(input_csv)

    corr = df.corr(numeric_only=True)

    corr.to_csv(output_csv)
    print("Correlation matrix saved to:", output_csv)
if __name__ == "__main__":
    compute_correlation(
        input_csv="data/intermediate/normalized_dataset.csv",
        output_csv="data/intermediate/correlation_matrix.csv"
    )