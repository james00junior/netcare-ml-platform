.PHONY: install lint test train evaluate serve clean pipeline

install:
	pip install -e ".[dev,api,monitoring]"

lint:
	ruff check src tests api || true
	black --check src tests api || true

format:
	black src tests api
	ruff check --fix src tests api || true

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

# Local training
train-baseline:
	python run_baseline.py

train-gbdt:
	python run_gbdt.py

evaluate:
	python -c "import pandas as pd; from src.models.evaluate import evaluate_both_models; \
lr=pd.read_csv('artifacts/baseline_model_predictions.csv'); \
gb=pd.read_csv('artifacts/gbdt_model_predictions.csv'); \
print(evaluate_both_models(lr, gb, output_dir='artifacts'))"

pipeline: train-baseline train-gbdt evaluate

serve:
	uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

validate-data:
	python -c "from src.data.ingestion import load_raw_data; from src.data.validation import run_data_quality_checks; run_data_quality_checks(load_raw_data()).print_report()"

preprocess:
	python -c "from src.data.ingestion import load_raw_data, save_processed_data; from src.features.build_features import build_feature_matrix; from src.data.preprocessing import train_test_split_data; from pathlib import Path; \
df=load_raw_data(); X,y=build_feature_matrix(df); Xtr,Xte,ytr,yte=train_test_split_data(X,y); \
Path('data/processed').mkdir(parents=True, exist_ok=True); \
save_processed_data(Xtr,'X_train'); save_processed_data(Xte,'X_test'); \
save_processed_data(ytr.to_frame(),'y_train'); save_processed_data(yte.to_frame(),'y_test'); print('done')"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov dist build *.egg-info
