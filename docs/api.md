# API Reference

Base URL (local): `http://localhost:8000`

## Endpoints

### `GET /health`

Health check.

**Response**
```json
{
  "status": "ok",
  "model_loaded": true,
  "model_version": "local-xgboost",
  "environment": "dev"
}
```

### `POST /predict`

Single patient prediction.

**Headers**
- `X-API-Key`: (optional if configured)

**Request**
```json
{
  "features": {
    "age": 67,
    "sex": "Female",
    "admission_type": "Emergency",
    "length_of_stay": 4,
    "creatinine": 1.2,
    "hemoglobin": 12.5,
    "has_diabetes": 1
  }
}
```

**Response**
```json
{
  "predicted_label": 1,
  "probability": 0.72,
  "model_version": "local-xgboost",
  "risk_tier": "high"
}
```

### `POST /predict/batch`

Batch prediction.

**Request**
```json
{
  "records": [
    {"age": 67, "sex": "Female", ...},
    {"age": 45, "sex": "Male", ...}
  ]
}
```

## Risk Tiers

| Probability | Tier |
|-------------|------|
| < 0.30 | low |
| 0.30 – 0.60 | medium |
| ≥ 0.60 | high |