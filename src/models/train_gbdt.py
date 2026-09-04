"""
Train HistGradientBoostingClassifier model.

Replacement for XGBoost – pure scikit-learn, no OpenMP required.
"""

from typing import Any

import joblib
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report, recall_score, roc_auc_score

from src.config.model_config import HistGBConfig


def train_gbdt_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    config: HistGBConfig | None = None,
) -> HistGradientBoostingClassifier:
    """Train HistGradientBoostingClassifier with project defaults."""
    config = config or HistGBConfig()

    model = HistGradientBoostingClassifier(
        max_iter=config.max_iter,
        max_depth=config.max_depth,
        learning_rate=config.learning_rate,
        min_samples_leaf=config.min_samples_leaf,
        l2_regularization=config.l2_regularization,
        max_bins=config.max_bins,
        early_stopping=config.early_stopping,
        validation_fraction=config.validation_fraction,
        n_iter_no_change=config.n_iter_no_change,
        random_state=config.random_state,
        class_weight=config.class_weight,
    )

    model.fit(X_train, y_train)
    return model


def predict_gbdt(
    model: HistGradientBoostingClassifier,
    X: pd.DataFrame,
) -> tuple[pd.Series, pd.Series]:
    """Return predicted labels and probabilities."""
    preds = pd.Series(model.predict(X), index=X.index, name="predicted")
    probs = pd.Series(model.predict_proba(X)[:, 1], index=X.index, name="probability")
    return preds, probs


def run_gbdt_training(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    config: HistGBConfig | None = None,
    save_path: str | None = None,
    preprocessor: Any = None,
) -> dict[str, Any]:
    """
    Full GBDT training + evaluation convenience function.

    The fitted preprocessing transformer is persisted alongside the model so
    inference can use exactly the same transformations learned from training.
    """
    config = config or HistGBConfig()
    model = train_gbdt_model(X_train, y_train, config)

    preds, probs = predict_gbdt(model, X_test)

    metrics = {
        "accuracy": float(accuracy_score(y_test, preds)),
        "roc_auc": float(roc_auc_score(y_test, probs)),
        "recall": float(recall_score(y_test, preds, zero_division=0)),
    }

    print("=" * 60)
    print("HistGradientBoosting Classifier")
    print("=" * 60)
    print(f"  Accuracy : {metrics['accuracy']:.4f}")
    print(f"  AUC-ROC  : {metrics['roc_auc']:.4f}")
    print(f"  Recall   : {metrics['recall']:.4f}")
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

    run_gbdt_training(
        X_train,
        X_test,
        y_train,
        y_test,
        save_path=str(out_dir / "gbdt_model_predictions.csv"),
    )
