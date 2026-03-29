from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
)


def compute_binary_metrics(y_true, y_pred, y_prob=None) -> Dict[str, Any]:
    """
    Compute metrics with FLAT structure for training code.
    Also includes imbalance-aware metrics for honest reporting.
    """
    n_pos = sum(y_true == 1)
    n_neg = sum(y_true == 0)
    n_total = len(y_true)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    
    # Compute all metrics
    accuracy = float(accuracy_score(y_true, y_pred))
    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    balanced_accuracy = float(balanced_accuracy_score(y_true, y_pred))
    mcc = float(matthews_corrcoef(y_true, y_pred))
    specificity = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
    sensitivity = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    
    roc_auc = None
    if y_prob is not None:
        try:
            roc_auc = float(roc_auc_score(y_true, y_prob))
        except Exception:
            roc_auc = None
    
    # FLAT STRUCTURE - training code expects these keys directly at top level
    metrics = {
        # Required by training code
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "roc_auc": roc_auc,
        
        # Additional for better reporting
        "balanced_accuracy": balanced_accuracy,
        "matthews_corrcoef": mcc,
        "specificity": specificity,
        "sensitivity": sensitivity,
        
        # Metadata for context
        "class_distribution": {
            "negative_class_0": int(n_neg),
            "positive_class_1": int(n_pos),
            "total": int(n_total),
            "positive_ratio": float(n_pos / n_total) if n_total > 0 else 0,
        },
        
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp),
        },
        
        "classification_report": classification_report(y_true, y_pred, output_dict=True, zero_division=0),
    }
    
    return metrics


def save_json(data: Dict[str, Any], out_path: str | Path) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def save_predictions(
    meta: pd.DataFrame,
    y_true,
    y_pred,
    y_prob,
    out_path: str | Path,
) -> None:
    out_df = meta.copy()
    out_df["y_true"] = list(y_true)
    out_df["y_pred"] = list(y_pred)
    if y_prob is not None:
        out_df["confidence_score"] = list(y_prob)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False)


def append_markdown_report(
    out_path: str | Path,
    task_name: str,
    best_model_name: str,
    metrics: Dict[str, Any],
) -> None:
    """Generate comprehensive markdown report with honest metrics."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    dist = metrics.get("class_distribution", {})
    cm = metrics.get("confusion_matrix", {})
    
    # Handle ROC-AUC formatting properly
    roc_auc_str = "N/A"
    if metrics.get('roc_auc') is not None:
        roc_auc_str = f"{metrics.get('roc_auc'):.4f}"
    
    lines = [
        f"## {task_name}",
        "",
        f"**Best Model:** {best_model_name}",
        "",
        "### Class Distribution",
        f"- Negative (0): {dist.get('negative_class_0', 'N/A')}",
        f"- Positive (1): {dist.get('positive_class_1', 'N/A')}",
        f"- Total: {dist.get('total', 'N/A')}",
        f"- Positive Ratio: {dist.get('positive_ratio', 0):.4f}",
        "",
        "### Standard Metrics",
        f"- Accuracy: {metrics.get('accuracy', 0):.4f}",
        f"- Precision: {metrics.get('precision', 0):.4f}",
        f"- Recall (Sensitivity): {metrics.get('recall', 0):.4f}",
        f"- F1-Score: {metrics.get('f1_score', 0):.4f}",
        f"- ROC-AUC: {roc_auc_str}",
        "",
        "### Imbalance-Aware Metrics ⭐",
        f"- **Balanced Accuracy: {metrics.get('balanced_accuracy', 0):.4f}** ← Use this instead!",
        f"- Matthews Correlation Coefficient: {metrics.get('matthews_corrcoef', 0):.4f}",
        f"- Specificity (TNR): {metrics.get('specificity', 0):.4f}",
        f"- Sensitivity (TPR): {metrics.get('sensitivity', 0):.4f}",
        "",
        "### Confusion Matrix",
        f"- True Negatives (TN): {cm.get('true_negatives', 0)}",
        f"- False Positives (FP): {cm.get('false_positives', 0)}",
        f"- False Negatives (FN): {cm.get('false_negatives', 0)}",
        f"- True Positives (TP): {cm.get('true_positives', 0)}",
        "",
    ]

    mode = "a" if out_path.exists() else "w"
    with open(out_path, mode, encoding="utf-8") as f:
        if mode == "w":
            f.write("# Evaluation Report\n\n")
        f.write("\n".join(lines))
        f.write("\n")