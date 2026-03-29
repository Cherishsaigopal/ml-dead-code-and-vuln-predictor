import pandas as pd
from src.integration.compiler_pipeline import SecureCompilerPipeline

# Extract features from test.cpp
pipeline = SecureCompilerPipeline()
features_df = pipeline._extract_features_from_file("test.cpp")

print("=" * 80)
print("FEATURES EXTRACTED FROM test.cpp:")
print("=" * 80)
print(f"Columns: {list(features_df.columns)}")
print(f"Total features: {len(features_df.columns)}")
print("\nFirst function features:")
print(features_df.iloc[0])

# Load training data
training_data = pd.read_csv("data/intermediate/normalized_dataset.csv")
print("\n" + "=" * 80)
print("FEATURES IN TRAINING DATA:")
print("=" * 80)
print(f"Columns: {list(training_data.columns)}")
print(f"Total features: {len(training_data.columns)}")

# Find mismatches
train_cols = set(training_data.columns)
extract_cols = set(features_df.columns) - {"function_id", "function_name", "file"}
missing_in_extract = train_cols - extract_cols
missing_in_train = extract_cols - train_cols

print(f"\nMissing in extraction: {missing_in_extract}")
print(f"Missing in training: {missing_in_train}")