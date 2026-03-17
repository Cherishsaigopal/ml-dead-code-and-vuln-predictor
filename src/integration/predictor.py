from __future__ import annotations

import joblib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd


@dataclass
class PredictionResult:
    function_id: str
    function_name: str
    file: str
    dead_prob: float
    dead_label: int
    vuln_prob: float
    vuln_label: int
    features_used: Dict[str, float]


class ModelPredictor:
    def __init__(self, model_dir: str = "models") -> None:
        self.model_dir = Path(model_dir)

        dead_bundle = self._load_bundle("best_deadcode_model.joblib")
        vuln_bundle = self._load_bundle("best_vuln_model.joblib")

        self.dead_model = self._extract_model(dead_bundle, "best_deadcode_model.joblib")
        self.vuln_model = self._extract_model(vuln_bundle, "best_vuln_model.joblib")

        self.dead_feature_columns = self._extract_feature_columns(
            dead_bundle, "best_deadcode_model.joblib"
        )
        self.vuln_feature_columns = self._extract_feature_columns(
            vuln_bundle, "best_vuln_model.joblib"
        )

    def _load_bundle(self, filename: str):
        path = self.model_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Required model file not found: {path}")
        return joblib.load(path)

    def _extract_model(self, bundle, filename: str):
        if not isinstance(bundle, dict):
            return bundle

        if "model" not in bundle:
            raise ValueError(
                f"'model' key not found inside {filename}. Available keys: {list(bundle.keys())}"
            )

        return bundle["model"]

    def _extract_feature_columns(self, bundle, filename: str) -> List[str]:
        if isinstance(bundle, dict) and "feature_columns" in bundle:
            cols = bundle["feature_columns"]
            if not isinstance(cols, list):
                raise ValueError(f"'feature_columns' must be a list in {filename}.")
            return cols

        model = self._extract_model(bundle, filename)
        if hasattr(model, "feature_names_in_"):
            return list(model.feature_names_in_)

        raise ValueError(f"Could not determine feature columns from {filename}.")

    def _align_features(self, df: pd.DataFrame, required_columns: List[str]) -> pd.DataFrame:
        aligned = df.copy()

        for col in required_columns:
            if col not in aligned.columns:
                aligned[col] = 0

        aligned = aligned[required_columns]

        for col in aligned.columns:
            aligned[col] = pd.to_numeric(aligned[col], errors="coerce").fillna(0)

        return aligned

    def _predict_proba_safe(self, model, X: pd.DataFrame) -> List[float]:
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(X)
            if probs.shape[1] == 2:
                return probs[:, 1].tolist()
            return probs[:, 0].tolist()

        preds = model.predict(X)
        return [float(p) for p in preds]

    def predict_dataframe(
        self,
        features_df: pd.DataFrame,
        metadata_columns: Optional[List[str]] = None,
    ) -> List[PredictionResult]:
        if metadata_columns is None:
            metadata_columns = ["function_id", "function_name", "file"]

        missing_meta = [c for c in metadata_columns if c not in features_df.columns]
        if missing_meta:
            raise ValueError(f"Missing required metadata columns: {missing_meta}")

        meta_df = features_df[metadata_columns].copy()
        raw_feature_df = features_df.drop(columns=metadata_columns, errors="ignore")

        X_dead = self._align_features(raw_feature_df, self.dead_feature_columns)
        X_vuln = self._align_features(raw_feature_df, self.vuln_feature_columns)

        dead_probs = self._predict_proba_safe(self.dead_model, X_dead)
        vuln_probs = self._predict_proba_safe(self.vuln_model, X_vuln)

        combined_cols = sorted(set(self.dead_feature_columns) | set(self.vuln_feature_columns))
        X_report = self._align_features(raw_feature_df, combined_cols)

        results: List[PredictionResult] = []
        for i in range(len(features_df)):
            feature_map = {col: float(X_report.iloc[i][col]) for col in X_report.columns}

            dead_prob = float(dead_probs[i])
            vuln_prob = float(vuln_probs[i])

            results.append(
                PredictionResult(
                    function_id=str(meta_df.iloc[i]["function_id"]),
                    function_name=str(meta_df.iloc[i]["function_name"]),
                    file=str(meta_df.iloc[i]["file"]),
                    dead_prob=dead_prob,
                    dead_label=1 if dead_prob >= 0.5 else 0,
                    vuln_prob=vuln_prob,
                    vuln_label=1 if vuln_prob >= 0.5 else 0,
                    features_used=feature_map,
                )
            )

        return results