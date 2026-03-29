import pandas as pd
from src.integration.predictor import ModelPredictor

# Load predictor
predictor = ModelPredictor(model_dir="models")

print("Dead Code Model expects these columns:")
print(predictor.dead_feature_columns)
print(f"\nTotal: {len(predictor.dead_feature_columns)}")

print("\n" + "="*80 + "\n")

print("Vulnerability Model expects these columns:")
print(predictor.vuln_feature_columns)
print(f"\nTotal: {len(predictor.vuln_feature_columns)}")

# Try predicting on a simple test case
print("\n" + "="*80 + "\n")

test_features = {
    "function_id": "test123",
    "function_name": "test_func",
    "file": "test.cpp",
}

# Add all required features with test values
for col in predictor.dead_feature_columns:
    if col not in test_features:
        test_features[col] = 1.0  # Default value

df = pd.DataFrame([test_features])
print("Test DataFrame shape:", df.shape)
print("Columns in df:", df.columns.tolist())

try:
    results = predictor.predict_dataframe(df)
    print("\n✓ Prediction successful!")
    result = results[0]
    print(f"  Dead Code Prob: {result.dead_prob:.4f}")
    print(f"  Vuln Prob: {result.vuln_prob:.4f}")
except Exception as e:
    print(f"\n❌ Prediction failed: {e}")