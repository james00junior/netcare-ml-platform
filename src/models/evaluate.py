"""
Model evaluation pack.

Extracted and refactored from deliverable_4_evaluation_pack.py.
"""

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


def compute_metrics(
    y_true: pd.Series | list,
    y_pred: pd.Series | list,
    y_prob: pd.Series | list,
    model_name: str = "model",
) -> dict[str, Any]:
    """Compute a comprehensive set of classification metrics."""
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

    return {
        "model": model_name,
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_prob)),
        "average_precision": float(average_precision_score(y_true, y_prob)),
        "true_negatives": int(tn),
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "true_positives": int(tp),
        "specificity": float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0,
        "n_test_samples": len(y_true),
        "positive_rate_actual": float(pd.Series(y_true).mean()),
    }


def evaluate_model(
    y_true: pd.Series,
    y_pred: pd.Series,
    y_prob: pd.Series,
    model_name: str = "model",
    output_dir: str | Path | None = None,
    prefix: str = "",
) -> dict[str, Any]:
    """
    Evaluate a single model and optionally save plots + metrics.
    """
    metrics = compute_metrics(y_true, y_pred, y_prob, model_name)

    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        # ROC
        fpr, tpr, _ = roc_curve(y_true, y_prob)
        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, label=f"{model_name} (AUC = {metrics['roc_auc']:.3f})", lw=2)
        plt.plot([0, 1], [0, 1], "k--", label="Random", lw=1)
        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.title(f"ROC Curve – {model_name}")
        plt.legend(loc="lower right")
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(out / f"{prefix}roc_curve.png", dpi=150)
        plt.close()

        # Precision-Recall
        prec, rec, _ = precision_recall_curve(y_true, y_prob)
        plt.figure(figsize=(8, 6))
        plt.plot(rec, prec, label=f"{model_name} (AP = {metrics['average_precision']:.3f})", lw=2)
        plt.xlabel("Recall")
        plt.ylabel("Precision")
        plt.title(f"Precision-Recall Curve – {model_name}")
        plt.legend(loc="upper right")
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(out / f"{prefix}precision_recall_curve.png", dpi=150)
        plt.close()

        # Confusion Matrix
        cm = confusion_matrix(y_true, y_pred)
        disp = ConfusionMatrixDisplay(
            confusion_matrix=cm,
            display_labels=["Not readmitted", "Readmitted ≤30d"],
        )
        _fig, ax = plt.subplots(figsize=(7, 6))
        disp.plot(cmap=plt.cm.Blues, ax=ax, values_format="d")
        ax.set_title(f"Confusion Matrix – {model_name}")
        plt.tight_layout()
        plt.savefig(out / f"{prefix}confusion_matrix.png", dpi=150)
        plt.close()

    return metrics


def evaluate_both_models(
    lr_predictions: pd.DataFrame,
    xgb_predictions: pd.DataFrame,
    output_dir: str | Path | None = None,
) -> pd.DataFrame:
    """
    Evaluate Logistic Regression and XGBoost side-by-side
    (logic from deliverable_4).
    """
    metrics_lr = compute_metrics(
        lr_predictions["actual"],
        lr_predictions["predicted"],
        lr_predictions["probability"],
        "Logistic Regression (Baseline)",
    )
    metrics_xgb = compute_metrics(
        xgb_predictions["actual"],
        xgb_predictions["predicted"],
        xgb_predictions["probability"],
        "XGBoost",
    )

    metrics_df = pd.DataFrame([metrics_lr, metrics_xgb])

    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        metrics_df.to_csv(out / "evaluation_metrics_summary.csv", index=False)

        # Combined ROC
        plt.figure(figsize=(8, 6))
        for df, name, color in [
            (lr_predictions, "Logistic Regression", "C0"),
            (xgb_predictions, "XGBoost", "C1"),
        ]:
            fpr, tpr, _ = roc_curve(df["actual"], df["probability"])
            auc = roc_auc_score(df["actual"], df["probability"])
            plt.plot(fpr, tpr, label=f"{name} (AUC = {auc:.3f})", lw=2, color=color)
        plt.plot([0, 1], [0, 1], "k--", label="Random", lw=1)
        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.title("ROC Curve – Baseline vs XGBoost")
        plt.legend(loc="lower right")
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(out / "roc_curve.png", dpi=150)
        plt.close()

        # Combined PR
        plt.figure(figsize=(8, 6))
        for df, name, color in [
            (lr_predictions, "Logistic Regression", "C0"),
            (xgb_predictions, "XGBoost", "C1"),
        ]:
            prec, rec, _ = precision_recall_curve(df["actual"], df["probability"])
            ap = average_precision_score(df["actual"], df["probability"])
            plt.plot(rec, prec, label=f"{name} (AP = {ap:.3f})", lw=2, color=color)
        plt.xlabel("Recall")
        plt.ylabel("Precision")
        plt.title("Precision-Recall Curve – Baseline vs XGBoost")
        plt.legend(loc="upper right")
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(out / "precision_recall_curve.png", dpi=150)
        plt.close()

        # Confusion matrices
        for preds, name, fname, cmap in [
            (xgb_predictions, "XGBoost", "confusion_matrix.png", plt.cm.Blues),
            (
                lr_predictions,
                "Logistic Regression (Baseline)",
                "confusion_matrix_baseline.png",
                plt.cm.Oranges,
            ),
        ]:
            cm = confusion_matrix(preds["actual"], preds["predicted"])
            disp = ConfusionMatrixDisplay(
                confusion_matrix=cm,
                display_labels=["Not readmitted", "Readmitted ≤30d"],
            )
            _fig, ax = plt.subplots(figsize=(7, 6))
            disp.plot(cmap=cmap, ax=ax, values_format="d")
            ax.set_title(f"Confusion Matrix – {name}")
            plt.tight_layout()
            plt.savefig(out / fname, dpi=150)
            plt.close()

        # Summary for best model
        best = metrics_xgb if metrics_xgb["roc_auc"] >= metrics_lr["roc_auc"] else metrics_lr
        summary = pd.DataFrame(
            {
                "metric": [
                    "Best Model",
                    "Accuracy",
                    "Precision",
                    "Recall (Sensitivity)",
                    "F1-Score",
                    "ROC-AUC",
                    "Average Precision (PR-AUC)",
                    "Specificity",
                    "True Positives",
                    "False Positives",
                    "True Negatives",
                    "False Negatives",
                    "Baseline (LR) ROC-AUC",
                    "Baseline (LR) Accuracy",
                ],
                "value": [
                    best["model"],
                    round(best["accuracy"], 4),
                    round(best["precision"], 4),
                    round(best["recall"], 4),
                    round(best["f1_score"], 4),
                    round(best["roc_auc"], 4),
                    round(best["average_precision"], 4),
                    round(best["specificity"], 4),
                    best["true_positives"],
                    best["false_positives"],
                    best["true_negatives"],
                    best["false_negatives"],
                    round(metrics_lr["roc_auc"], 4),
                    round(metrics_lr["accuracy"], 4),
                ],
            }
        )
        summary.to_csv(out / "deliverable_4_summary.csv", index=False)

    return metrics_df


if __name__ == "__main__":
    from pathlib import Path

    lr = pd.read_csv("artifacts/baseline_model_predictions.csv")
    xgb = pd.read_csv("artifacts/xgboost_model_predictions.csv")

    metrics = evaluate_both_models(lr, xgb, output_dir="artifacts")
    print(
        metrics[["model", "accuracy", "precision", "recall", "f1_score", "roc_auc"]].to_string(
            index=False
        )
    )
    print("\nAll evaluation artefacts generated.")
