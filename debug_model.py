import joblib
from pathlib import Path

# Load vulnerability model
vuln_bundle = joblib.load("models/best_vuln_model.joblib")
vuln_model = vuln_bundle["model"]
vuln_features = vuln_bundle["feature_columns"]

print("Vulnerability Model Expected Features:")
print(f"Total features: {len(vuln_features)}")
for i, feat in enumerate(vuln_features, 1):
    print(f"  {i}. {feat}")

print("\n" + "="*80 + "\n")

# Load dead code model
dead_bundle = joblib.load("models/best_deadcode_model.joblib")
dead_model = dead_bundle["model"]
dead_features = dead_bundle["feature_columns"]

print("Dead Code Model Expected Features:")
print(f"Total features: {len(dead_features)}")
for i, feat in enumerate(dead_features, 1):
    print(f"  {i}. {feat}")

# Check if they match
print("\n" + "="*80)
if vuln_features == dead_features:
    print("✓ Both models use same features")
else:
    print("⚠️  Models use DIFFERENT features!")
    vuln_only = set(vuln_features) - set(dead_features)
    dead_only = set(dead_features) - set(vuln_features)
    if vuln_only:
        print(f"   Vuln only: {vuln_only}")
    if dead_only:
        print(f"   Dead only: {dead_only}")