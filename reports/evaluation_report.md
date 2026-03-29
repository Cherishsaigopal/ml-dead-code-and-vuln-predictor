# Evaluation Report

## Dead Code Prediction

**Best Model:** XGBoost

### Class Distribution
- Negative (0): 923
- Positive (1): 192
- Total: 1115
- Positive Ratio: 0.1722

### Standard Metrics
- Accuracy: 0.9910
- Precision: 0.9740
- Recall (Sensitivity): 0.9740
- F1-Score: 0.9740
- ROC-AUC: 0.9983

### Imbalance-Aware Metrics ⭐
- **Balanced Accuracy: 0.9843** ← Use this instead!
- Matthews Correlation Coefficient: 0.9685
- Specificity (TNR): 0.9946
- Sensitivity (TPR): 0.9740

### Confusion Matrix
- True Negatives (TN): 918
- False Positives (FP): 5
- False Negatives (FN): 5
- True Positives (TP): 187

## Vulnerability Prediction

**Best Model:** RandomForest

### Class Distribution
- Negative (0): 1056
- Positive (1): 59
- Total: 1115
- Positive Ratio: 0.0529

### Standard Metrics
- Accuracy: 0.9462
- Precision: 0.4953
- Recall (Sensitivity): 0.8983
- F1-Score: 0.6386
- ROC-AUC: 0.9798

### Imbalance-Aware Metrics ⭐
- **Balanced Accuracy: 0.9236** ← Use this instead!
- Matthews Correlation Coefficient: 0.6439
- Specificity (TNR): 0.9489
- Sensitivity (TPR): 0.8983

### Confusion Matrix
- True Negatives (TN): 1002
- False Positives (FP): 54
- False Negatives (FN): 6
- True Positives (TP): 53

