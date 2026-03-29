import joblib
import pandas as pd

df = pd.read_csv('data/intermediate/normalized_dataset.csv')
dead_model_bundle = joblib.load('models/best_deadcode_model.joblib')
vuln_model_bundle = joblib.load('models/best_vuln_model.joblib')

print('=== TRAINING DATA ===')
print('Total samples:', len(df))
print('Dead code samples (label=1):', (df['label_deadcode'] == 1).sum())
print('Vuln samples (label=1):', (df['label_vuln'] == 1).sum())
print()
print('Sample features:')
print(df[['function_name', 'loc', 'cyclomatic', 'sensitive_api_calls', 'label_deadcode', 'label_vuln']].head(10))
print()
print('=== MODEL FEATURES ===')
print('Dead code features:', dead_model_bundle['feature_columns'])
print('Vuln features:', vuln_model_bundle['feature_columns'])