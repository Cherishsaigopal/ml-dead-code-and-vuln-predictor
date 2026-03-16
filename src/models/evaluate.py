from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def compute_binary_metrics(y_true, y_pred, y_prob=None) -> Dict[str, Any]:
    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_true, y_pred, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
        "classification_report": classification_report(
            y_true,
            y_pred,
            zero_division=0,
            output_dict=True,
        ),
    }

    if y_prob is not None:
        try:
            metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob))
        except Exception:
            metrics["roc_auc"] = None
    else:
        metrics["roc_auc"] = None

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
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"## {task_name}",
        "",
        f"**Best Model:** {best_model_name}",
        "",
        f"- Accuracy: {metrics['accuracy']:.4f}",
        f"- Precision: {metrics['precision']:.4f}",
        f"- Recall: {metrics['recall']:.4f}",
        f"- F1-Score: {metrics['f1_score']:.4f}",
        f"- ROC-AUC: {metrics['roc_auc'] if metrics['roc_auc'] is not None else 'N/A'}",
        f"- Confusion Matrix: {metrics['confusion_matrix']}",
        "",
    ]

    mode = "a" if out_path.exists() else "w"
    with open(out_path, mode, encoding="utf-8") as f:
        if mode == "w":
            f.write("# Evaluation Report\n\n")
        f.write("\n".join(lines))
        f.write("\n")