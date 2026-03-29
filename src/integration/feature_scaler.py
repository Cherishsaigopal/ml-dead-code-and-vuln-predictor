import joblib
from pathlib import Path
import pandas as pd

class FeatureScaler:
    """Load and apply the same normalization used during training."""
    
    def __init__(self, model_dir: str = "models"):
        self.model_dir = Path(model_dir)
        self.scaler = self._load_scaler()
    
    def _load_scaler(self):
        """Load the fitted scaler from training."""
        scaler_path = self.model_dir / "feature_scaler.joblib"
        if scaler_path.exists():
            return joblib.load(scaler_path)
        return None
    
    def scale(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply normalization to features."""
        if self.scaler is None:
            print("⚠️ WARNING: Scaler not found. Returning raw features.")
            return df
        
        numeric_cols = df.select_dtypes(include=['number']).columns
        df_scaled = df.copy()
        df_scaled[numeric_cols] = self.scaler.transform(df[numeric_cols])
        return df_scaled