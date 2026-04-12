import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

feature_columns = [
    'loc', 'cyclomatic', 'branch_count', 'loop_count', 'max_nesting_depth',
    'call_count', 'return_count', 'basic_blocks', 'cfg_edges',
    'unreachable_blocks', 'unreachable_ratio',
    'sensitive_api_calls', 'high_risk_api_flag',
    'commit_count', 'churn'
]

print("⏳ Generating Training Data with Git History Correlation...")
samples = []

for _ in range(2500):
    # 1. SAFE CODE: Low Churn, Few Commits, No Bad APIs
    samples.append({
        'loc': np.random.randint(5, 50), 'cyclomatic': np.random.randint(1, 5),
        'branch_count': np.random.randint(0, 3), 'loop_count': np.random.randint(0, 3),
        'max_nesting_depth': np.random.randint(1, 3), 'call_count': np.random.randint(1, 5),
        'return_count': 1, 'basic_blocks': np.random.randint(1, 5), 'cfg_edges': np.random.randint(1, 5),
        'unreachable_blocks': 0, 'unreachable_ratio': 0.0,
        'sensitive_api_calls': 0, 'high_risk_api_flag': 0,
        'commit_count': np.random.randint(1, 10),  # LOW GIT ACTIVITY
        'churn': np.random.randint(0, 50),         # LOW CHURN
        'label_vuln': 0, 'label_deadcode': 0
    })

    # 2. VULNERABLE ONLY: High Churn, High Commits, Bad APIs
    samples.append({
        'loc': np.random.randint(20, 150), 'cyclomatic': np.random.randint(3, 15),
        'branch_count': np.random.randint(2, 10), 'loop_count': np.random.randint(1, 5),
        'max_nesting_depth': np.random.randint(2, 6), 'call_count': np.random.randint(3, 10),
        'return_count': np.random.randint(1, 4), 'basic_blocks': np.random.randint(5, 20), 'cfg_edges': np.random.randint(5, 25),
        'unreachable_blocks': 0, 'unreachable_ratio': 0.0,
        'sensitive_api_calls': np.random.randint(1, 5), 'high_risk_api_flag': 1,
        'commit_count': np.random.randint(20, 150), # HIGH GIT ACTIVITY
        'churn': np.random.randint(200, 1000),      # HIGH CHURN (Bugs introduced over time)
        'label_vuln': 1, 'label_deadcode': 0
    })

    # 3. DEAD CODE ONLY: Medium/High Churn (Refactored code), Unreachable Blocks
    samples.append({
        'loc': np.random.randint(20, 100), 'cyclomatic': np.random.randint(2, 10),
        'branch_count': np.random.randint(1, 5), 'loop_count': np.random.randint(0, 4),
        'max_nesting_depth': np.random.randint(1, 4), 'call_count': np.random.randint(1, 8),
        'return_count': np.random.randint(1, 3), 'basic_blocks': np.random.randint(3, 15), 'cfg_edges': np.random.randint(3, 18),
        'unreachable_blocks': np.random.randint(1, 5), 'unreachable_ratio': np.random.uniform(0.1, 0.5),
        'sensitive_api_calls': 0, 'high_risk_api_flag': 0,
        'commit_count': np.random.randint(15, 80),  # REFACTORED FREQUENTLY
        'churn': np.random.randint(100, 500),       # LEFTOVER DEAD VARIABLES
        'label_vuln': 0, 'label_deadcode': 1
    })

    # 4. MIXED (VULN + DEAD CODE): Very High Churn/Commits
    samples.append({
        'loc': np.random.randint(30, 200), 'cyclomatic': np.random.randint(5, 20),
        'branch_count': np.random.randint(3, 12), 'loop_count': np.random.randint(1, 6),
        'max_nesting_depth': np.random.randint(2, 7), 'call_count': np.random.randint(4, 15),
        'return_count': np.random.randint(1, 5), 'basic_blocks': np.random.randint(10, 30), 'cfg_edges': np.random.randint(10, 40),
        'unreachable_blocks': np.random.randint(1, 6), 'unreachable_ratio': np.random.uniform(0.1, 0.6),
        'sensitive_api_calls': np.random.randint(1, 6), 'high_risk_api_flag': 1,
        'commit_count': np.random.randint(50, 200), # VERY HIGH GIT ACTIVITY
        'churn': np.random.randint(500, 2000),      # VERY HIGH CHURN
        'label_vuln': 1, 'label_deadcode': 1
    })

df = pd.DataFrame(samples).sample(frac=1).reset_index(drop=True)
X = df[feature_columns]
y_vuln = df['label_vuln']
y_dead = df['label_deadcode']

os.makedirs('models', exist_ok=True)
scaler = StandardScaler()
X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=feature_columns)
joblib.dump(scaler, 'models/feature_scaler.joblib')

print("⚙️ Training Git-Aware Vulnerability Model...")
model_vuln = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42)
model_vuln.fit(X_scaled, y_vuln)
joblib.dump({"model": model_vuln, "feature_columns": feature_columns, "target": "label_vuln"}, 'models/best_vuln_model.joblib')

print("⚙️ Training Git-Aware Dead Code Model...")
model_dead = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42)
model_dead.fit(X_scaled, y_dead)
joblib.dump({"model": model_dead, "feature_columns": feature_columns, "target": "label_deadcode"}, 'models/best_deadcode_model.joblib')

metadata = {"features_used": feature_columns}
with open('models/vuln_model_metadata.json', 'w') as f: json.dump(metadata, f)
with open('models/deadcode_model_metadata.json', 'w') as f: json.dump(metadata, f)

print("✅ Success! Git-aware generalized models ready.")