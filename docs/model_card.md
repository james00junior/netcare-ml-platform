# Model Card – 30-Day Hospital Readmission

## Model Details

- **Name**: netcare-readmission-model
- **Type**: Binary classifier (readmitted within 30 days)
- **Algorithms**: Logistic Regression (baseline), XGBoost (primary)
- **Framework**: scikit-learn, XGBoost
- **Owner**: Netcare ML Team

## Intended Use

- **Primary**: Risk stratification of patients at discharge for 30-day readmission.
- **Users**: Clinical care coordinators, discharge planners, quality teams.
- **Out of scope**: Real-time triage in emergency settings; diagnostic decisions.

## Training Data

- Source: Hospital readmissions dataset (assessment)
- Target: `readmitted_30d`
- Preprocessing: identifier/leakage drop, categorical standardisation, median lab imputation, one-hot encoding
- Split: 70/30 stratified

## Metrics (Assessment)

See `evaluation_metrics_summary.csv` for the latest numbers from the assessment run.

Key metrics tracked:
- ROC-AUC (primary)
- Precision / Recall / F1
- Specificity
- Average Precision (PR-AUC)

## Limitations

- Trained on a single assessment dataset; generalisation to new facilities requires validation.
- Does not currently incorporate free-text clinical notes or real-time streaming features.
- Risk tiers are heuristic thresholds and should be calibrated with clinical stakeholders.

## Ethical Considerations

- Model outputs are decision-support only; final clinical judgment remains with the care team.
- Monitor for disparate impact across demographic groups (sex, age bands, payer type).
- Audit logs retained for all production predictions.

## Version History

| Version | Date | Notes |
|---------|------|-------|
| 0.1.0 | 2026-09 | Initial extraction from assessment scripts |