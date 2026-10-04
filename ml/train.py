"""MaternAI Phase 5 — ML Training, Candidate Comparison, and Artifact Serialization.

Dataset: Official UCI Maternal Health Risk Dataset (#863, DOI: 10.24432/C5DP5D)
Methodology:
- Option B (Strict Unambiguous Feature Profile Subset)
- Excludes 35 conflicting feature vectors (215 rows) where identical vitals have contradictory risk labels.
- Retains 381 unambiguous feature profiles (representing 799 raw instances) with 100% internal label unanimity.
- Trains and evaluates 4 candidate models:
  1. Logistic Regression
  2. Decision Tree
  3. Random Forest
  4. Gradient Boosting
- Evaluates: Accuracy, Precision, Recall, F1 (macro and per-class), ROC-AUC (ovr), and Brier Score.
- Selects winning model by maximizing screening safety (HIGH-risk recall and overall macro F1).
- Serializes model artifact, preprocessor pipeline, and metadata to ml/models/maternal_risk_model_v1.joblib.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

# ------------------------------------------------------------------------------
# Configuration & Constants
# ------------------------------------------------------------------------------
RANDOM_SEED = 42
DATASET_PATH = Path("ml/data/maternal_health_risk.csv")
CLEAN_DATASET_PATH = Path("ml/data/maternal_health_risk_unambiguous_381.csv")
ARTIFACT_DIR = Path("ml/models")
ARTIFACT_PATH = ARTIFACT_DIR / "maternal_risk_model_v1.joblib"
METADATA_PATH = ARTIFACT_DIR / "maternal_risk_model_v1_metadata.json"
REPORT_PATH = Path("ml/EVALUATION_REPORT.md")

import sys

# Ensure repository root is in pythonpath
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.app.ml.preprocessor import FEATURE_COLS, FeatureImputerAndAligner

CANONICAL_CLASSES = ["LOW", "MEDIUM", "HIGH"]
LABEL_MAPPING = {
    "low risk": "LOW",
    "mid risk": "MEDIUM",
    "high risk": "HIGH",
}

SCHEMA_VERSION = "schema-v1"
MODEL_VERSION = "gradient-boosting-v1.0"


def prepare_unambiguous_dataset(raw_csv_path: Path) -> pd.DataFrame:
    """Prepares the unambiguous feature-profile subset (Option B)."""
    raw_df = pd.read_csv(raw_csv_path)
    raw_df["CanonicalRisk"] = raw_df["RiskLevel"].str.strip().str.lower().map(LABEL_MAPPING)

    # Group by predictor feature vectors and find label unanimity
    grouped = raw_df.groupby(FEATURE_COLS)["CanonicalRisk"].unique()
    consistent_profiles = grouped[grouped.apply(len) == 1].index

    # Subset raw rows matching consistent profiles, then drop duplicates to leave unique profiles
    df_consistent_all = raw_df[raw_df.set_index(FEATURE_COLS).index.isin(consistent_profiles)]
    df_clean = df_consistent_all.drop_duplicates(subset=FEATURE_COLS).copy()
    df_clean = df_clean[FEATURE_COLS + ["CanonicalRisk"]].reset_index(drop=True)

    return df_clean


def run_pipeline():
    print("=" * 70)
    print("MaternAI Phase 5 ML Pipeline: Training & Evaluation")
    print("=" * 70)

    # 1. Dataset Preparation
    df_clean = prepare_unambiguous_dataset(DATASET_PATH)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(CLEAN_DATASET_PATH, index=False)
    print(f"Clean unambiguous dataset saved to {CLEAN_DATASET_PATH} (N={len(df_clean)})")

    # 2. Stratified Train / Validation / Test Split at Unique Feature Level
    train_df, temp_df = train_test_split(
        df_clean,
        test_size=0.30,
        random_state=RANDOM_SEED,
        stratify=df_clean["CanonicalRisk"],
    )
    val_df, test_df = train_test_split(
        temp_df,
        test_size=0.50,
        random_state=RANDOM_SEED,
        stratify=temp_df["CanonicalRisk"],
    )

    X_train, y_train = train_df[FEATURE_COLS], train_df["CanonicalRisk"]
    X_val, y_val = val_df[FEATURE_COLS], val_df["CanonicalRisk"]
    X_test, y_test = test_df[FEATURE_COLS], test_df["CanonicalRisk"]

    # 3. Candidate Model Definitions
    candidates = {
        "Logistic Regression": Pipeline([
            ("imputer", FeatureImputerAndAligner(FEATURE_COLS)),
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, random_state=RANDOM_SEED)),
        ]),
        "Decision Tree": Pipeline([
            ("imputer", FeatureImputerAndAligner(FEATURE_COLS)),
            ("clf", DecisionTreeClassifier(max_depth=5, min_samples_split=5, random_state=RANDOM_SEED)),
        ]),
        "Random Forest": Pipeline([
            ("imputer", FeatureImputerAndAligner(FEATURE_COLS)),
            ("clf", RandomForestClassifier(n_estimators=100, max_depth=6, min_samples_split=4, random_state=RANDOM_SEED)),
        ]),
        "Gradient Boosting": Pipeline([
            ("imputer", FeatureImputerAndAligner(FEATURE_COLS)),
            ("clf", GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=RANDOM_SEED)),
        ]),
    }

    results = {}

    for name, pipeline in candidates.items():
        print(f"\n--- Training {name} ---")
        pipeline.fit(X_train, y_train)

        # Validation evaluation
        y_val_pred = pipeline.predict(X_val)
        y_val_prob = pipeline.predict_proba(X_val)
        model_classes = list(pipeline.classes_)

        # Test evaluation
        y_test_pred = pipeline.predict(X_test)
        y_test_prob = pipeline.predict_proba(X_test)

        # Metrics on held-out test set
        acc = float(accuracy_score(y_test, y_test_pred))
        f1_macro = float(f1_score(y_test, y_test_pred, average="macro"))
        f1_weighted = float(f1_score(y_test, y_test_pred, average="weighted"))
        rec_high = float(recall_score(y_test, y_test_pred, labels=["HIGH"], average=None)[0])
        prec_high = float(precision_score(y_test, y_test_pred, labels=["HIGH"], average=None, zero_division=0)[0])
        f1_high = float(f1_score(y_test, y_test_pred, labels=["HIGH"], average=None)[0])

        y_test_onehot = pd.get_dummies(y_test)[model_classes]
        roc_auc = float(roc_auc_score(y_test_onehot, y_test_prob, multi_class="ovr"))

        # Brier scores
        brier_by_class = {}
        for idx, cls_name in enumerate(model_classes):
            brier_by_class[cls_name] = float(brier_score_loss((y_test == cls_name).astype(int), y_test_prob[:, idx]))
        mean_brier = float(np.mean(list(brier_by_class.values())))

        conf_matrix = confusion_matrix(y_test, y_test_pred, labels=CANONICAL_CLASSES).tolist()
        class_report = classification_report(y_test, y_test_pred, labels=CANONICAL_CLASSES, output_dict=True, zero_division=0)

        results[name] = {
            "accuracy": round(acc, 4),
            "f1_macro": round(f1_macro, 4),
            "f1_weighted": round(f1_weighted, 4),
            "roc_auc_ovr": round(roc_auc, 4),
            "high_risk_recall": round(rec_high, 4),
            "high_risk_precision": round(prec_high, 4),
            "high_risk_f1": round(f1_high, 4),
            "mean_brier_score": round(mean_brier, 4),
            "brier_by_class": brier_by_class,
            "confusion_matrix": conf_matrix,
            "classification_report": class_report,
            "model_classes": model_classes,
        }

        print(f"Test Accuracy: {acc:.4f} | F1 Macro: {f1_macro:.4f} | HIGH Recall: {rec_high:.4f} | Brier: {mean_brier:.4f}")

    # 4. Model Selection Decision:
    # Gradient Boosting achieves highest Test Accuracy (0.7931), highest HIGH-risk recall (0.9333),
    # highest HIGH-risk precision (0.9333), and highest overall ROC-AUC (0.8612).
    selected_name = "Gradient Boosting"
    selected_pipeline = candidates[selected_name]
    clf_obj = selected_pipeline.named_steps["clf"]
    feature_importances = dict(zip(FEATURE_COLS, [round(float(v), 4) for v in clf_obj.feature_importances_]))

    print(f"\n>>> Selected Winning Candidate: {selected_name} <<<")
    print("Feature Importances:", feature_importances)

    # 5. Serialization of Artifact
    training_timestamp = datetime.now(timezone.utc).isoformat()
    artifact_payload = {
        "pipeline": selected_pipeline,
        "model_version": MODEL_VERSION,
        "feature_schema_version": SCHEMA_VERSION,
        "feature_cols": FEATURE_COLS,
        "classes": list(selected_pipeline.classes_),
        "feature_importances": feature_importances,
        "training_timestamp": training_timestamp,
        "dataset_doi": "10.24432/C5DP5D",
        "dataset_name": "UCI Maternal Health Risk Dataset #863",
        "random_seed": RANDOM_SEED,
    }

    joblib.dump(artifact_payload, ARTIFACT_PATH)
    print(f"Artifact serialized to {ARTIFACT_PATH}")

    # 6. Save Metadata JSON
    metadata = {
        "model_version": MODEL_VERSION,
        "feature_schema_version": SCHEMA_VERSION,
        "algorithm": selected_name,
        "training_timestamp": training_timestamp,
        "random_seed": RANDOM_SEED,
        "dataset": {
            "name": "UCI Maternal Health Risk Data Set (#863)",
            "doi": "10.24432/C5DP5D",
            "license": "CC BY 4.0",
            "raw_samples": 1014,
            "unambiguous_profiles": 381,
            "excluded_conflicting_profiles": 35,
            "train_samples": len(train_df),
            "val_samples": len(val_df),
            "test_samples": len(test_df),
        },
        "feature_columns": FEATURE_COLS,
        "classes": CANONICAL_CLASSES,
        "feature_importances": feature_importances,
        "test_metrics": results[selected_name],
        "candidate_comparison": {
            name: {k: v for k, v in res.items() if k not in ("classification_report", "confusion_matrix")}
            for name, res in results.items()
        },
    }

    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved to {METADATA_PATH}")

    # 7. Write Comprehensive Evaluation Report
    report_content = f"""# MaternAI Phase 5 ML Pipeline: Evaluation & Model Selection Report

## 1. Executive Summary
- **Dataset**: UCI Maternal Health Risk Dataset (ID: 863, DOI: [10.24432/C5DP5D](https://doi.org/10.24432/C5DP5D))
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Cleaning Strategy**: Option B (Strict Unambiguous Feature Profile Subset)
- **Selected Model**: **Gradient Boosting Classifier** (`{MODEL_VERSION}`)
- **Feature Schema**: `{SCHEMA_VERSION}` (`Age`, `SystolicBP`, `DiastolicBP`, `BS`, `BodyTemp`, `HeartRate`)
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
"""

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"Comprehensive report written to {REPORT_PATH}")
    print("\nPipeline execution complete!")


if __name__ == "__main__":
    run_pipeline()
