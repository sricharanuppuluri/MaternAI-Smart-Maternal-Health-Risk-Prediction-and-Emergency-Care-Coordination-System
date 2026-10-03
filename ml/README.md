# Machine Learning Service & Pipeline

This directory contains ML datasets, training scripts, model artifacts, and evaluation reports for MaternAI.

## Status

- **Phase 0**: Architectural boundary established. No model training, dataset synthesis, or clinical interpretation performed.
- **Phase 5 (Planned)**: Dataset preparation, model training, model comparison, evaluation, explainability, and versioning.

## Candidate Models

The documented candidate models to be evaluated during the ML phase:
1. Logistic Regression
2. Decision Tree
3. Random Forest
4. Gradient Boosting

## Future ML Input Contract

The documented input contract (`MLRiskInput`) is defined in `backend/app/schemas/ml.py`:
- `age_years`: float | None
- `hemoglobin`: float | None
- `systolic_bp`: float | None
- `diastolic_bp`: float | None
- `blood_sugar`: float | None
- `weight_kg`: float | None
- `pregnancy_week`: int | None
- `symptom_features`: dict[str, int | float | bool]

## Guiding Principles

- ML predicts structured risk (LOW, MEDIUM, HIGH); it does NOT diagnose.
- The model is a screening/decision-support component.
- The model selection must be backed by documented metrics (accuracy, precision, recall, F1, confusion matrix, calibration).
- Safety rules take precedence over ML predictions and LLM generation.
