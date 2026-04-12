import os, numpy as np, pandas as pd

os.makedirs('data/intermediate', exist_ok=True)
samples = []
feature_columns = [
    'loc', 'cyclomatic', 'branch_count', 'loop_count', 'max_nesting_depth',
    'call_count', 'return_count', 'basic_blocks', 'cfg_edges',
    'unreachable_blocks', 'unreachable_ratio',
    'sensitive_api_calls', 'high_risk_api_flag',
    'commit_count', 'churn'
]

def add_sample(feats, vuln, dead):
    row = {'sample_id': 'id', 'file_name': 'f.c', 'function_name': 'func'}
    row.update(feats)
    row['label_vuln'] = vuln        # Note the repo expects 'label_vuln'
    row['label_deadcode'] = dead    # Note the repo expects 'label_deadcode'
    samples.append(row)

for i in range(150): # Vulnerable
    add_sample({c: np.random.randint(1, 10) for c in feature_columns}, 1, 0)
for i in range(150): # Dead code
    add_sample({c: np.random.randint(1, 10) for c in feature_columns}, 0, 1)
for i in range(250): # Safe
    add_sample({c: np.random.randint(1, 10) for c in feature_columns}, 0, 0)

df = pd.DataFrame(samples).fillna(0)
# The repository's training script expects this file to exist
df.to_csv('data/intermediate/normalized_dataset.csv', index=False)
print("✅ Generated normalized_dataset.csv locally!")