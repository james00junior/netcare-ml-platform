"""
Train Logistic Regression baseline model.

Extracted from deliverable_3_baseline_model.py.
"""

from typing import Any

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.config.model_config import BaselineConfig


def train_baseline_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    config: BaselineConfig | None = None,
) -> Pipeline:
    """
    Train the required Logistic Regression baseline.

    Returns a fitted sklearn Pipeline (scaler + classifier).
    """
    config = config or BaselineConfig()

    model = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    max_iter=config.max_iter,
                    class_weight=config.class_weight,
                    random_state=config.random_state,
                    solver=config.solver,
                ),
            ),
        ]
    )

    model.fit(X_train, y_train)
    return model


def predict_baseline(
    model: Pipeline,
    X: pd.DataFrame,
) -> tuple[pd.Series, pd.Series]:
    """Return predicted labels and probabilities."""
    preds = pd.Series(model.predict(X), index=X.index, name="predicted")
    probs = pd.Series(model.predict_proba(X)[:, 1], index=X.index, name="probability")
    return preds, probs


def run_baseline_training(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    config: BaselineConfig | None = None,
    save_path: str | None = None,
    preprocessor: Any = None,
) -> dict[str, Any]:
    """
    Full baseline training + evaluation convenience function.

    The fitted preprocessing transformer is persisted alongside the model so
    inference can use exactly the same transformations learned from training.
    """
    config = config or BaselineConfig()
    model = train_baseline_model(X_train, y_train, config)

    preds, probs = predict_baseline(model, X_test)

    metrics = {
        "accuracy": float(accuracy_score(y_test, preds)),
        "roc_auc": float(roc_auc_score(y_test, probs)),
    }

    print("=" * 60)
    print("BASELINE – Logistic Regression")
    print("=" * 60)
    print(f"  Accuracy : {metrics['accuracy']:.4f}")
    print(f"  AUC-ROC  : {metrics['roc_auc']:.4f}")
    print(classification_report(y_test, preds, digits=3))

    predictions = pd.DataFrame(
        {
            "actual": y_test.values,
            "predicted": preds.values,
            "probability": probs.values,
        }
    )

    if save_path:
        predictions.to_csv(save_path, index=False)
        print(f"Saved predictions: {save_path}")

    model_path = None
    preprocessor_path = None
    if save_path:
        model_path = save_path.replace(".csv", ".joblib")
        joblib.dump(model, model_path)
        print(f"Saved model: {model_path}")

        if preprocessor is not None:
            preprocessor_path = save_path.replace(
                "_predictions.csv",
                "_preprocessor.joblib",
            )
            joblib.dump(preprocessor, preprocessor_path)
            print(f"Saved preprocessor: {preprocessor_path}")

    return {
        "model": model,
        "metrics": metrics,
        "predictions": predictions,
        "model_path": model_path,
        "preprocessor_path": preprocessor_path,
    }


if __name__ == "__main__":
    from pathlib import Path

    from src.data.ingestion import load_raw_data
    from src.data.preprocessing import train_test_split_data
    from src.features.build_features import build_feature_matrix

    df = load_raw_data()
    X, y = build_feature_matrix(df)
    X_train, X_test, y_train, y_test = train_test_split_data(X, y)

    out_dir = Path("artifacts")
    out_dir.mkdir(exist_ok=True)

    run_baseline_training(
        X_train,
        X_test,
        y_train,
        y_test,
        save_path=str(out_dir / "baseline_model_predictions.csv"),
    )
