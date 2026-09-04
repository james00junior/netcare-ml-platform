#!/usr/bin/env python
"""
Full local pipeline:

  1. Data quality assessment
  2. Feature building + train/test split
  3. Train Logistic Regression baseline
  4. Train HistGradientBoosting (primary model)
  5. Evaluate both models and write artefacts
"""

from pathlib import Path

from src.data.ingestion import load_raw_data
from src.data.validation import run_data_quality_checks
from src.data.preprocessing import prepare_train_test_data
from src.models.train_baseline import run_baseline_training
from src.models.train_gbdt import run_gbdt_training
from src.models.evaluate import evaluate_both_models


def main() -> None:
    artifacts = Path("artifacts")
    artifacts.mkdir(exist_ok=True)

    # 1. Load + data quality
    print("\n" + "=" * 60)
    print("STEP 1 – Data quality assessment")
    print("=" * 60)
    df = load_raw_data()
    report = run_data_quality_checks(df)
    report.print_report()

    # 2. Features + split
    print("\n" + "=" * 60)
    print("STEP 2 – Feature engineering + train/test split")
    print("=" * 60)
    preprocessor, X_train, X_test, y_train, y_test = prepare_train_test_data(df)
    print(f"Features: {X_train.shape[1]}")
    print(f"Train: {X_train.shape[0]} rows | Test: {X_test.shape[0]} rows")
    print(f"Target rate – train: {y_train.mean():.3f} | test: {y_test.mean():.3f}")

    # 3. Baseline
    print("\n" + "=" * 60)
    print("STEP 3 – Train Logistic Regression baseline")
    print("=" * 60)
    baseline_result = run_baseline_training(
        X_train,
        X_test,
        y_train,
        y_test,
        save_path=str(artifacts / "baseline_model_predictions.csv"),
        preprocessor=preprocessor,
    )

    # 4. HistGradientBoosting
    print("\n" + "=" * 60)
    print("STEP 4 – Train HistGradientBoosting")
    print("=" * 60)
    gbdt_result = run_gbdt_training(
        X_train,
        X_test,
        y_train,
        y_test,
        save_path=str(artifacts / "gbdt_model_predictions.csv"),
        preprocessor=preprocessor,
    )

    # 5. Evaluation
    print("\n" + "=" * 60)
    print("STEP 5 – Evaluation pack")
    print("=" * 60)
    lr_preds = baseline_result["predictions"]
    gb_preds = gbdt_result["predictions"]

    metrics_df = evaluate_both_models(lr_preds, gb_preds, output_dir=str(artifacts))

    metrics_df = metrics_df.copy()
    metrics_df.loc[metrics_df["model"].str.contains("XGBoost", na=False), "model"] = (
        "HistGradientBoosting"
    )
    metrics_df.loc[
        metrics_df["model"].str.contains("Logistic", na=False), "model"
    ] = "Logistic Regression (Baseline)"

    print(
        "\n" + metrics_df[
            ["model", "accuracy", "precision", "recall", "f1_score", "roc_auc"]
        ].to_string(index=False)
    )

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"Artefacts written to: {artifacts.resolve()}")
    print("  - baseline_model_predictions.csv / .joblib / _preprocessor.joblib")
    print("  - gbdt_model_predictions.csv / .joblib / _preprocessor.joblib")
    print("  - evaluation_metrics_summary.csv")
    print("  - roc_curve.png / precision_recall_curve.png / confusion_matrix*.png")


if __name__ == "__main__":
    main()
