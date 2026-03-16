from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description="Run inference with a saved model")
    parser.add_argument("--model", required=True, help="Path to .joblib model file")
    parser.add_argument("--input", required=True, help="CSV file with features")
    parser.add_argument("--output", default="reports/inference_output.csv")
    args = parser.parse_args()

    bundle = joblib.load(args.model)
    model = bundle["model"]
    feature_columns = bundle["feature_columns"]
    target_name = bundle.get("target", "prediction")

    df = pd.read_csv(args.input)
    df.columns = [str(c).strip() for c in df.columns]

    rename_map = {}
    if "file" in df.columns and "file_name" not in df.columns:
        rename_map["file"] = "file_name"
    if "function" in df.columns and "function_name" not in df.columns:
        rename_map["function"] = "function_name"
    if rename_map:
        df = df.rename(columns=rename_map)

    missing = [c for c in feature_columns if c not in df.columns]
    if missing:
        raise ValueError(f"Missing feature columns in input CSV: {missing}")

    X = df[feature_columns].copy()
    for col in feature_columns:
        X[col] = pd.to_numeric(X[col], errors="coerce")

    y_pred = model.predict(X)

    out_df = df.copy()
    out_df[f"predicted_{target_name}"] = y_pred

    if hasattr(model, "predict_proba"):
        out_df["confidence_score"] = model.predict_proba(X)[:, 1]

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(output_path, index=False)

    print(f"[OK] Predictions saved to: {output_path}")


if __name__ == "__main__":
    main()