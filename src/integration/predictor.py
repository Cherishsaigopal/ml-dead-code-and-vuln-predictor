from __future__ import annotations

import joblib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import json


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
    # Default features used during training
    DEFAULT_FEATURES = [
        'loc', 'cyclomatic', 'branch_count', 'loop_count', 'max_nesting_depth',
        'call_count', 'return_count', 'basic_blocks', 'cfg_edges',
        'unreachable_blocks', 'unreachable_ratio',
        'sensitive_api_calls', 'high_risk_api_flag',
        'commit_count', 'churn'
    ]

    def __init__(self, model_dir: str = "models") -> None:
        self.model_dir = Path(model_dir)
        
        # ✅ Load scaler for feature normalization
        self.scaler = self._load_scaler()

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

    def _load_scaler(self):
        """Load the fitted scaler from training."""
        scaler_path = self.model_dir / "feature_scaler.joblib"
        if scaler_path.exists():
            scaler = joblib.load(scaler_path)
            print(f"✅ Loaded feature scaler from {scaler_path}")
            return scaler
        else:
            print(f"⚠️  WARNING: Scaler not found at {scaler_path}. Features will NOT be normalized!")
            return None

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
        """Extract feature columns from bundle or model. Uses fallback if needed."""
        
        # Try dict with feature_columns key
        if isinstance(bundle, dict) and "feature_columns" in bundle:
            cols = bundle["feature_columns"]
            if isinstance(cols, list):
                return cols
        
        # Try dict with features_used key
        if isinstance(bundle, dict) and "features_used" in bundle:
            cols = bundle["features_used"]
            if isinstance(cols, list):
                return cols
        
        # Try to get from model object
        try:
            model = self._extract_model(bundle, filename)
            if hasattr(model, "feature_names_in_"):
                return list(model.feature_names_in_)
        except Exception as e:
            print(f"⚠️  Could not extract from model object: {e}")
        
        # Fallback: use default features
        print(f"⚠️  Using default feature list for {filename}")
        return self.DEFAULT_FEATURES

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
        
        if not self.validate_features(features_df):
            raise ValueError("Feature set validation failed!")

        if metadata_columns is None:
            # Use the ACTUAL column names from extraction
            metadata_columns = ["sample_id", "function_name", "file_name"]

        missing_meta = [c for c in metadata_columns if c not in features_df.columns]
        if missing_meta:
            raise ValueError(f"Missing required metadata columns: {missing_meta}")

        meta_df = features_df[metadata_columns].copy()
        raw_feature_df = features_df.drop(columns=metadata_columns, errors="ignore")

        # ✅ SCALE FEATURES BEFORE PREDICTION
        if self.scaler is not None:
            # Get the feature names the scaler was fit with (from the model)
            scaler_feature_names = list(self.scaler.feature_names_in_)
            
            # Filter raw features to ONLY those the scaler knows about
            features_to_scale = [col for col in scaler_feature_names if col in raw_feature_df.columns]
            missing = set(scaler_feature_names) - set(features_to_scale)
            
            if missing:
                raise ValueError(
                    f"Missing required features for scaling: {missing}\n"
                    f"Scaler expects: {sorted(scaler_feature_names)}\n"
                    f"Got: {sorted(raw_feature_df.columns)}"
                )
            
            raw_feature_df_scaled = raw_feature_df.copy()
            raw_feature_df_scaled[features_to_scale] = self.scaler.transform(raw_feature_df[features_to_scale])
            print(f"✅ Applied scaler to {len(features_to_scale)} features")
        else:
            raw_feature_df_scaled = raw_feature_df.copy()
            print(f"⚠️  WARNING: Using raw features (not normalized)")

        X_dead = self._align_features(raw_feature_df_scaled, self.dead_feature_columns)
        X_vuln = self._align_features(raw_feature_df_scaled, self.vuln_feature_columns)

        dead_probs = self._predict_proba_safe(self.dead_model, X_dead)
        vuln_probs = self._predict_proba_safe(self.vuln_model, X_vuln)

        combined_cols = sorted(set(self.dead_feature_columns) | set(self.vuln_feature_columns))
        X_report = self._align_features(raw_feature_df_scaled, combined_cols)

        results: List[PredictionResult] = []
        for i in range(len(features_df)):
            feature_map = {col: float(X_report.iloc[i][col]) for col in X_report.columns}

            dead_prob = float(dead_probs[i])
            vuln_prob = float(vuln_probs[i])

            # Map back to PredictionResult column names
            results.append(
                PredictionResult(
                    function_id=str(meta_df.iloc[i]["sample_id"]),  # sample_id → function_id
                    function_name=str(meta_df.iloc[i]["function_name"]),
                    file=str(meta_df.iloc[i]["file_name"]),  # file_name → file
                    dead_prob=dead_prob,
                    dead_label=1 if dead_prob >= 0.5 else 0,
                    vuln_prob=vuln_prob,
                    vuln_label=1 if vuln_prob >= 0.5 else 0,
                    features_used=feature_map,
                )
            )

        return results
    
    def validate_features(self, df: pd.DataFrame) -> bool:
        """Validate that input features match training features."""
        
        # Load metadata
        dead_meta_path = self.model_dir / "deadcode_model_metadata.json"
        vuln_meta_path = self.model_dir / "vuln_model_metadata.json"
        
        if not dead_meta_path.exists() or not vuln_meta_path.exists():
            print("⚠️  WARNING: Model metadata not found. Skipping validation.")
            return True
        
        with open(dead_meta_path) as f:
            dead_meta = json.load(f)
        with open(vuln_meta_path) as f:
            vuln_meta = json.load(f)
        
        # Check dead code features
        dead_features_expected = set(dead_meta.get("features_used", self.DEFAULT_FEATURES))
        dead_features_actual = set(self.dead_feature_columns)
        
        if dead_features_expected != dead_features_actual:
            print(f"⚠️  DEAD CODE feature mismatch (continuing anyway)")
            print(f"  Expected: {sorted(dead_features_expected)}")
            print(f"  Got:      {sorted(dead_features_actual)}")
        
        # Check vuln features
        vuln_features_expected = set(vuln_meta.get("features_used", self.DEFAULT_FEATURES))
        vuln_features_actual = set(self.vuln_feature_columns)
        
        if vuln_features_expected != vuln_features_actual:
            print(f"⚠️  VULNERABILITY feature mismatch (continuing anyway)")
            print(f"  Expected: {sorted(vuln_features_expected)}")
            print(f"  Got:      {sorted(vuln_features_actual)}")
        
        print("✅ Feature validation PASSED")
        return True