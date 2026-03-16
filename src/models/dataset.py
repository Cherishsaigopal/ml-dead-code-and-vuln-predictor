from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import pandas as pd


EXPECTED_FEATURE_COLUMNS = [
    "loc",
    "cyclomatic",
    "branch_count",
    "loop_count",
    "max_nesting_depth",
    "call_count",
    "return_count",
    "basic_blocks",
    "cfg_edges",
    "unreachable_blocks",
    "unreachable_ratio",
    "sensitive_api_calls",
    "high_risk_api_flag",
    "commit_count",
    "churn",
]


def load_dataset(csv_path: str | Path) -> pd.DataFrame:
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset not found: {csv_path}")

    df = pd.read_csv(csv_path)
    df.columns = [str(c).strip() for c in df.columns]

    rename_map = {}
    if "file" in df.columns and "file_name" not in df.columns:
        rename_map["file"] = "file_name"
    if "function" in df.columns and "function_name" not in df.columns:
        rename_map["function"] = "function_name"

    if rename_map:
        df = df.rename(columns=rename_map)

    return df


def get_feature_columns(df: pd.DataFrame) -> List[str]:
    available = [c for c in EXPECTED_FEATURE_COLUMNS if c in df.columns]
    if not available:
        raise ValueError(
            "No expected feature columns found in dataset. "
            f"Expected from: {EXPECTED_FEATURE_COLUMNS}"
        )
    return available


def get_metadata(df: pd.DataFrame) -> pd.DataFrame:
    meta_cols = [c for c in ["sample_id", "file_name", "function_name"] if c in df.columns]
    if not meta_cols:
        return pd.DataFrame(index=df.index)
    return df[meta_cols].copy()


def get_features_and_target(
    df: pd.DataFrame,
    target_col: str
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, List[str]]:
    if target_col not in df.columns:
        raise ValueError(f"Missing required target column: {target_col}")

    feature_cols = get_feature_columns(df)

    X = df[feature_cols].copy()
    for col in feature_cols:
        X[col] = pd.to_numeric(X[col], errors="coerce")

    y = pd.to_numeric(df[target_col], errors="coerce").fillna(0).astype(int)
    y = y.apply(lambda v: 1 if v == 1 else 0)

    meta = get_metadata(df)

    return X, y, meta, feature_cols