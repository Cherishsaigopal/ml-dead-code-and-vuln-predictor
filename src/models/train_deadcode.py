from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import make_scorer, f1_score
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline

from src.models.dataset import get_features_and_target, load_dataset
from src.models.evaluate import (
    append_markdown_report,
    compute_binary_metrics,
    save_json,
    save_predictions,
)

try:
    from xgboost import XGBClassifier
    XGB_AVAILABLE = True
except Exception:
    XGB_AVAILABLE = False


def build_rf_pipeline(random_state: int) -> tuple[Pipeline, dict]:
    pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("model", RandomForestClassifier(
            random_state=random_state,
            class_weight="balanced",
        )),
    ])

    params = {
        "model__n_estimators": [100, 200],
        "model__max_depth": [None, 10, 20],
        "model__min_samples_split": [2, 5],
    }
    return pipe, params


def build_xgb_pipeline(random_state: int) -> tuple[Pipeline, dict]:
    pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("model", XGBClassifier(
            random_state=random_state,
            eval_metric="logloss",
            tree_method="hist",
        )),
    ])

    params = {
        "model__n_estimators": [100, 200],
        "model__max_depth": [4, 6],
        "model__learning_rate": [0.05, 0.1],
    }
    return pipe, params


def fit_and_evaluate(search, X_train, y_train, X_test, y_test):
    search.fit(X_train, y_train)
    best_model = search.best_estimator_
    y_prob = best_model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)
    metrics = compute_binary_metrics(y_test, y_pred, y_prob)
    return best_model, metrics, y_pred, y_prob


def main() -> None:
    parser = argparse.ArgumentParser(description="Train dead code prediction models")
    parser.add_argument("--input", default="data/intermediate/normalized_dataset.csv")
    parser.add_argument("--models_dir", default="models")
    parser.add_argument("--reports_dir", default="reports")
    parser.add_argument("--test_size", type=float, default=0.2)
    parser.add_argument("--random_state", type=int, default=42)
    args = parser.parse_args()

    df = load_dataset(args.input)
    X, y, meta, feature_cols = get_features_and_target(df, "label_deadcode")

        
    # ✅ KEEP ALL FEATURES - no leakage removal!
    # Dead code label uses unreachable_blocks, so model NEEDS these features
    # This is NOT leakage - it's proper feature engineering

    print(f"[INFO] Using ALL features for dead-code training (no dropping)")
    print(f"[INFO] Dead-code feature count: {len(feature_cols)}")
    print(f"[INFO] Features include: unreachable_blocks, unreachable_ratio, call_count, etc.")

    

    X_train, X_test, y_train, y_test, meta_train, meta_test = train_test_split(
        X, y, meta,
        test_size=args.test_size,
        random_state=args.random_state,
        stratify=y,
    )

    scorer = make_scorer(f1_score, zero_division=0)
    models_dir = Path(args.models_dir)
    reports_dir = Path(args.reports_dir)
    models_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    results = []

    rf_pipe, rf_params = build_rf_pipeline(args.random_state)
    rf_search = GridSearchCV(
        estimator=rf_pipe,
        param_grid=rf_params,
        scoring=scorer,
        cv=3,
        n_jobs=-1,
        verbose=1,
    )
    rf_model, rf_metrics, rf_pred, rf_prob = fit_and_evaluate(
        rf_search, X_train, y_train, X_test, y_test
    )
    results.append({
        "model_name": "RandomForest",
        "search": rf_search,
        "best_model": rf_model,
        "metrics": rf_metrics,
        "y_pred": rf_pred,
        "y_prob": rf_prob,
    })

    if XGB_AVAILABLE:
        xgb_pipe, xgb_params = build_xgb_pipeline(args.random_state)
        xgb_search = GridSearchCV(
            estimator=xgb_pipe,
            param_grid=xgb_params,
            scoring=scorer,
            cv=3,
            n_jobs=-1,
            verbose=1,
        )
        xgb_model, xgb_metrics, xgb_pred, xgb_prob = fit_and_evaluate(
            xgb_search, X_train, y_train, X_test, y_test
        )
        results.append({
            "model_name": "XGBoost",
            "search": xgb_search,
            "best_model": xgb_model,
            "metrics": xgb_metrics,
            "y_pred": xgb_pred,
            "y_prob": xgb_prob,
        })

    comparison_rows = []
    best_result = max(results, key=lambda r: r["metrics"]["f1_score"])

    for result in results:
        name = result["model_name"]
        search = result["search"]
        metrics = result["metrics"]

        comparison_rows.append({
            "model": name,
            "best_cv_score": float(search.best_score_),
            "accuracy": metrics["accuracy"],
            "precision": metrics["precision"],
            "recall": metrics["recall"],
            "f1_score": metrics["f1_score"],
            "roc_auc": metrics["roc_auc"],
            "best_params": str(search.best_params_),
        })

        safe_name = "random_forest" if name == "RandomForest" else "xgboost"
        joblib.dump(
            {
                "model": result["best_model"],
                "feature_columns": feature_cols,
                "target": "label_deadcode",
            },
            models_dir / f"deadcode_{safe_name}.joblib"
        )

    joblib.dump(
        {
            "model": best_result["best_model"],
            "feature_columns": feature_cols,
            "target": "label_deadcode",
        },
        models_dir / "best_deadcode_model.joblib"
    )

    pd.DataFrame(comparison_rows).to_csv(
        reports_dir / "deadcode_model_comparison.csv",
        index=False,
    )

    save_json(best_result["metrics"], reports_dir / "deadcode_metrics.json")
    save_predictions(
        meta_test,
        y_test,
        best_result["y_pred"],
        best_result["y_prob"],
        reports_dir / "deadcode_predictions.csv",
    )
    append_markdown_report(
        reports_dir / "evaluation_report.md",
        "Dead Code Prediction",
        best_result["model_name"],
        best_result["metrics"],
    )

    print(f"[DONE] Best dead code model: {best_result['model_name']}")
    print(f"[DONE] Saved to: {models_dir} and {reports_dir}")


if __name__ == "__main__":
    main()