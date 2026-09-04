"""Run baseline training (Logistic Regression)."""
from pathlib import Path

from src.data.ingestion import load_raw_data
from src.features.build_features import build_feature_matrix
from src.data.preprocessing import train_test_split_data
from src.models.train_baseline import run_baseline_training


def main():
    df = load_raw_data()
    print("Loaded data:", df.shape)

    X, y = build_feature_matrix(df)
    X_train, X_test, y_train, y_test = train_test_split_data(X, y)
    print(f"Train: {X_train.shape} | Test: {X_test.shape}")

    out_dir = Path("artifacts")
    out_dir.mkdir(exist_ok=True)

    result = run_baseline_training(
        X_train,
        X_test,
        y_train,
        y_test,
        save_path=str(out_dir / "baseline_model_predictions.csv"),
    )
    print("\nBaseline metrics:", result["metrics"])


if __name__ == "__main__":
    main()
