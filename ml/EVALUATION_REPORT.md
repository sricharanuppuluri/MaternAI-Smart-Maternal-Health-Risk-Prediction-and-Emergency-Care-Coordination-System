# MaternAI Phase 5 ML Pipeline: Evaluation & Model Selection Report

## 1. Executive Summary
- **Dataset**: UCI Maternal Health Risk Dataset (ID: 863, DOI: [10.24432/C5DP5D](https://doi.org/10.24432/C5DP5D))
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Cleaning Strategy**: Option B (Strict Unambiguous Feature Profile Subset)
- **Selected Model**: **Gradient Boosting Classifier** (`gradient-boosting-v1.0`)
- **Selection Basis**: Strictly chosen using the **validation partition** ($N=57$), with the test set held out until final evaluation.
- **Feature Schema**: `schema-v1` (`Age`, `SystolicBP`, `DiastolicBP`, `BS`, `BodyTemp`, `HeartRate`)
- **Held-Out Test Results ($N=58$, Point Estimates & 95% Bootstrap CIs, $B=1,000$, Seed=42)**:
  - **Accuracy**: **79.31%** (95% CI: [68.97%, 89.66%])
  - **Macro F1**: **0.7090** (95% CI: [0.5857, 0.8220])
  - **HIGH-Risk Recall**: **93.33%** (14/15) (95% CI: [77.78%, 100.00%])
  - **HIGH-Risk Precision**: **93.33%** (14/15) (95% CI: [77.78%, 100.00%])
  - **Multi-class ROC-AUC (OvR)**: **0.8612**
  - **Mean Multi-class Brier Score Loss**: **0.1069**

---

## 2. Dataset Provenance & Integrity (Option B)
- **Raw Instances**: 1,014 rows, 0 nulls.
- **Unique Predictor Feature Profiles**: 416
- **Profiles with 100% Consistent Risk Labels**: **381 vectors** (representing 799 raw instances)
- **Profiles with Contradictory Risk Labels**: **35 vectors** (representing 215 raw instances)
- **Exclusion Policy**: All 35 conflicting profiles (215 rows) were excluded. No majority voting, no tie-breaking heuristics, and no synthetic profile generation were used.
- **Modeling Population**: Exactly **381 unique feature profiles**.
- **Cross-Partition Leakage Verification**: Feature overlap between train, validation, and test partitions: **EXACTLY ZERO**.

### Class Distribution (N=381)
- `LOW`: 204 (53.54%)
- `HIGH`: 101 (26.51%)
- `MEDIUM`: 76 (19.95%)

### Partition Split
- **Train (70%)**: 266 profiles (`LOW`: 142, `HIGH`: 71, `MEDIUM`: 53)
- **Validation (15%)**: 57 profiles (`LOW`: 31, `HIGH`: 15, `MEDIUM`: 11)
- **Test (15%)**: 58 profiles (`LOW`: 31, `HIGH`: 15, `MEDIUM`: 12)

---

## 3. Model Selection Methodology (Validation Partition, N=57)
Candidate architectures were trained on the training partition ($N=266$) and evaluated exclusively on the **validation partition** ($N=57$) to guide model selection. The test set was strictly held out and untouched during this selection.

| Candidate Model | Val Accuracy | Val Macro F1 | Val HIGH Recall | Val HIGH Precision | Val ROC-AUC (OvR) | Val Brier Score |
|---|---|---|---|---|---|---|
| **Logistic Regression** | 70.18% | 0.5584 | 80.00% | 66.67% | 0.7874 | 0.1416 |
| **Decision Tree** | 71.93% | 0.6868 | 80.00% | 100.00% | 0.8307 | 0.1352 |
| **Random Forest** | 68.42% | 0.5656 | 73.33% | 84.62% | 0.8333 | 0.1225 |
| **Gradient Boosting** | **70.18%** | **0.6617** | **73.33%** | **91.67%** | **0.8792** | **0.1202** |

**Selection Decision**: **Gradient Boosting** was selected and frozen because it achieved the highest discrimination ability on the validation partition (ROC-AUC **0.8792**), lowest multi-class Brier score loss (**0.1202**), and strong HIGH risk precision (**91.67%**).

---

## 4. Final Evaluation & Uncertainty Reporting (Held-Out Test Set, N=58)
The frozen Gradient Boosting model was evaluated exactly once on the held-out test partition ($N=58$).

### 4.1 Performance Point Estimates & 95% Bootstrap Confidence Intervals ($B=1,000$, Seed=42)

| Metric | Point Estimate | Lower 95% CI | Upper 95% CI | Evaluation Sample Count |
|---|---|---|---|---|
| **Accuracy** | **79.31%** | 68.97% | 89.66% | $N = 58$ |
| **Macro F1** | **0.7090** | 0.5857 | 0.8220 | $N = 58$ |
| **HIGH-Risk Recall** | **93.33%** | 77.78% | 100.00% | $N_{HIGH} = 15$ |
| **HIGH-Risk Precision** | **93.33%** | 77.78% | 100.00% | $N_{HIGH} = 15$ |
| **Multi-class ROC-AUC (OvR)** | **0.8612** | — | — | $N = 58$ |
| **Mean Brier Score Loss** | **0.1069** | — | — | $N = 58$ |

### 4.2 Test Confusion Matrix
Rows = Ground Truth, Columns = Predicted (`[LOW, MEDIUM, HIGH]`):
```text
           Predicted LOW  Predicted MEDIUM  Predicted HIGH
Actual LOW            29                  1                1
Actual MEDIUM           9                  3                0
Actual HIGH             0                  1              14
```
- **HIGH-Risk Sensitivity**: 14 out of 15 HIGH-risk cases correctly classified (**93.33%**). Zero HIGH-risk cases were misclassified as LOW risk.
- **LOW-Risk Specificity**: 29 out of 31 LOW-risk cases correctly classified (**93.55%**).

---

## 5. Model Attribution & Calibration Notes
1. **Global Feature Importances (Tree Gain Attribution)**:
   - `BS` (Blood Sugar): **41.25%**
   - `SystolicBP`: **27.34%**
   - `BodyTemp`: **12.93%**
   - `Age`: **9.68%**
   - `DiastolicBP`: **5.02%**
   - `HeartRate`: **3.79%**
2. **Neutral Calibration Assessment**:
   - The multi-class Brier score loss is 0.1069 across 3 classes.
   - Due to the small test sample size ($N=58$, with only 12 MEDIUM and 15 HIGH instances), well-calibrated class probability estimates are **NOT** claimed. The model score is an internal screening metric and must not be interpreted as an authoritative medical probability.
3. **No Unsafe Directional Heuristics**:
   - Ad-hoc directional comparisons against fixed population medians (such as labeling low BP or adolescent age as 'risk decreasing') have been removed from the provider implementation.

---

## 6. Safety & Non-Diagnostic Clinical Notice
1. **Decision Support Only**: MaternAI provides maternal decision support and risk screening triage. It does **not** provide clinical diagnosis or prescription.
2. **Deterministic Safety Precedence**: `SafetyEngine` runs strictly before ML evaluation. The model output can never downgrade or dismiss an emergency safety event.
3. **Internal Metric**: `model_score` reflects internal model certainty (0.0 to 1.0) and is **never** presented as an authoritative medical probability.
4. **Population Limitation**: Dataset was collected in rural Bangladesh. It serves as an assistive screening prototype and has not been clinically validated for Indian populations.
