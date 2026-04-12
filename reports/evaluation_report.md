# Evaluation Report

## Dead Code Prediction

**Best Model:** RandomForest

### Class Distribution
- Negative (0): 80
- Positive (1): 30
- Total: 110
- Positive Ratio: 0.2727

### Standard Metrics
- Accuracy: 0.6909
- Precision: 0.0000
- Recall (Sensitivity): 0.0000
- F1-Score: 0.0000
- ROC-AUC: 0.4537

### Imbalance-Aware Metrics ⭐
- **Balanced Accuracy: 0.4750** ← Use this instead!
- Matthews Correlation Coefficient: -0.1190
- Specificity (TNR): 0.9500
- Sensitivity (TPR): 0.0000

### Confusion Matrix
- True Negatives (TN): 76
- False Positives (FP): 4
- False Negatives (FN): 30
- True Positives (TP): 0

## Vulnerability Prediction

**Best Model:** XGBoost

### Class Distribution
- Negative (0): 80
- Positive (1): 30
- Total: 110
- Positive Ratio: 0.2727

### Standard Metrics
- Accuracy: 0.6636
- Precision: 0.2667
- Recall (Sensitivity): 0.1333
- F1-Score: 0.1778
- ROC-AUC: 0.5221

### Imbalance-Aware Metrics ⭐
- **Balanced Accuracy: 0.4979** ← Use this instead!
- Matthews Correlation Coefficient: -0.0054
- Specificity (TNR): 0.8625
- Sensitivity (TPR): 0.1333

### Confusion Matrix
- True Negatives (TN): 69
- False Positives (FP): 11
- False Negatives (FN): 26
- True Positives (TP): 4

