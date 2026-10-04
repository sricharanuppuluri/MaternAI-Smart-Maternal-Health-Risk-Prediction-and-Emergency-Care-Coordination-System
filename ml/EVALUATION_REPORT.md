# MaternAI Phase 5 ML Pipeline: Evaluation & Model Selection Report

## 1. Executive Summary
- **Dataset**: UCI Maternal Health Risk Dataset (ID: 863, DOI: [10.24432/C5DP5D](https://doi.org/10.24432/C5DP5D))
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Cleaning Strategy**: Option B (Strict Unambiguous Feature Profile Subset)
- **Selected Model**: **Gradient Boosting Classifier** (`gradient-boosting-v1.0`)
- **Feature Schema**: `schema-v1` (`Age`, `SystolicBP`, `DiastolicBP`, `BS`, `BodyTemp`, `HeartRate`)
- **Key Test Metrics (Held-out N=58)**:
  - Accuracy: **79.31%**
  - Macro F1: **0.7090**
  - **HIGH-Risk Recall**: **93.33%** (14 of 15 high-risk cases detected)
  - **HIGH-Risk Precision**: **93.33%**
  - ROC-AUC (ovr): **0.8612**
  - Mean Multi-class Brier Score: **0.1069**

---

## 2. Dataset Provenance & Integrity
- **Raw Instances**: 1,014 rows, 0 nulls.
- **Duplicate Analysis**:
  - Unique predictor feature vectors: 416
  - Unambiguous feature profiles (identical labels across duplicates): **381 vectors** (799 total rows)
  - Conflicting feature profiles (different clinics assigned contradictory risk levels): **35 vectors** (215 rows)
- **Leakage Control (Option B)**:
  - Excluded the 35 ambiguous profiles.
  - Retained the 381 unambiguous feature profiles.
  - Zero duplicate feature vectors exist in the clean modeling dataset.
  - Train/Validation/Test split executed strictly at the unique profile level (Stratified 70/15/15, Seed=42).
  - Feature overlap between train, validation, and test partitions: **EXACTLY ZERO**.

### Class Distribution (Clean 381 Population)
- `LOW`: 204 (53.54%)
- `HIGH`: 101 (26.51%)
- `MEDIUM`: 76 (19.95%)

### Partition Split
- **Train (70%)**: 266 profiles (`LOW`: 142, `HIGH`: 71, `MEDIUM`: 53)
- **Validation (15%)**: 57 profiles (`LOW`: 31, `HIGH`: 15, `MEDIUM`: 11)
- **Test (15%)**: 58 profiles (`LOW`: 31, `HIGH`: 15, `MEDIUM`: 12)

---

## 3. Candidate Model Comparison (Held-Out Test Set N=58)

| Candidate Model | Accuracy | Macro F1 | Weighted F1 | ROC-AUC (ovr) | HIGH Recall | HIGH Precision | Mean Brier |
|---|---|---|---|---|---|---|---|
| **Logistic Regression** | 63.79% | 0.5070 | 0.5971 | 0.7058 | 60.00% | 69.23% | 0.1770 |
| **Decision Tree** | 77.59% | 0.7406 | 0.7765 | 0.8453 | 86.67% | 92.86% | 0.1192 |
| **Random Forest** | 74.14% | 0.6122 | 0.6888 | 0.8616 | 93.33% | 87.50% | 0.1145 |
| **Gradient Boosting** | **79.31%** | **0.7090** | **0.7637** | **0.8612** | **93.33%** | **93.33%** | **0.1069** |

---

## 4. Confusion Matrix (Gradient Boosting on Test Set)
Rows = Ground Truth, Columns = Predicted (`[LOW, MEDIUM, HIGH]`):
```text
           Predicted LOW  Predicted MEDIUM  Predicted HIGH
Actual LOW            29                 1               1
Actual MEDIUM          9                 3               0
Actual HIGH            0                 1              14
```
- **HIGH-Risk Sensitivity**: 14 out of 15 HIGH-risk cases correctly classified (**93.33%**). Zero HIGH-risk cases were misclassified as LOW risk.
- **LOW-Risk Specificity**: 29 out of 31 LOW-risk cases correctly classified (**93.55%**).

---

## 5. Feature Importances (Gradient Boosting)
1. **Blood Sugar (`BS`)**: 41.25%
2. **Systolic BP (`SystolicBP`)**: 27.34%
3. **Body Temperature (`BodyTemp`)**: 12.93%
4. **Age (`Age`)**: 9.68%
5. **Diastolic BP (`DiastolicBP`)**: 5.02%
6. **Heart Rate (`HeartRate`)**: 3.79%

---

## 6. Safety & Non-Diagnostic Clinical Notice
1. **Decision Support Only**: MaternAI provides maternal decision support and risk screening triage. It does **not** provide clinical diagnosis or prescription.
2. **Deterministic Safety Precedence**: `SafetyEngine` runs strictly before ML evaluation. The model output can never downgrade or dismiss an emergency safety event.
3. **Internal Metric**: `model_score` reflects internal model certainty (0.0 to 1.0) and is **never** presented as an authoritative medical probability.
4. **Population Limitation**: Dataset was collected in rural Bangladesh. It serves as a machine learning benchmark prototype and has not been clinically validated for Indian populations.
