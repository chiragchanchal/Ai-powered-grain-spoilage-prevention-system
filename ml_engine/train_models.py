"""
Model Training and Calibration Script for AI Spoilage Risk Engine.
Trains dual ensemble:
1. scikit-learn RandomForestClassifier (interpretable tabular trees, feature importance)
2. Neural Network MLPClassifier (deep non-linear risk interactions)
Validates High-Risk Recall against CS002 Benchmark (>= 90%) and serializes artifacts.
"""

import os
import json
import joblib
import datetime
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, recall_score, f1_score

from .dataset_generator import generate_grain_spoilage_dataset
from .feature_pipeline import FEATURE_NAMES

MODEL_DIR = os.path.join(os.path.dirname(__file__), "saved_models")


def train_and_evaluate_models():
    os.makedirs(MODEL_DIR, exist_ok=True)
    print("=" * 60)
    print("AI GRAIN SPOILAGE PREVENTION SYSTEM — MODEL TRAINING PIPELINE")
    print("=" * 60)

    # 1. Generate Dataset
    print("[1/5] Synthesizing physically validated grain microclimate dataset...")
    X, y, df = generate_grain_spoilage_dataset(n_samples=6000, random_seed=42)
    print(f"      Total records: {len(X)} across 9 features. Class balance: {np.bincount(y)}")

    # 2. Train / Test Split
    print("[2/5] Creating stratified 80/20 train/test split...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=42
    )

    # Fit Scaler for Neural Network
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 3. Train Random Forest Classifier
    print("[3/5] Fitting Scikit-Learn RandomForestClassifier (120 estimators)...")
    rf_model = RandomForestClassifier(
        n_estimators=120,
        max_depth=12,
        class_weight="balanced",
        min_samples_split=4,
        random_state=42,
        n_jobs=-1,
    )
    rf_model.fit(X_train, y_train)
    y_pred_rf = rf_model.predict(X_test)

    # 4. Train Deep Neural Network (MLP)
    print("[4/5] Fitting Deep Neural Network MLP (64x32 hidden layers)...")
    mlp_model = MLPClassifier(
        hidden_layer_sizes=(64, 32),
        activation="relu",
        solver="adam",
        max_iter=300,
        early_stopping=True,
        n_iter_no_change=15,
        random_state=42,
    )
    mlp_model.fit(X_train_scaled, y_train)
    y_pred_mlp = mlp_model.predict(X_test_scaled)

    # 5. Evaluate Ensemble
    print("[5/5] Evaluating dual-model ensemble and CS002 benchmarks...")
    p_rf = rf_model.predict_proba(X_test)
    p_mlp = mlp_model.predict_proba(X_test_scaled)
    p_ensemble = 0.55 * p_rf + 0.45 * p_mlp
    y_pred_ensemble = np.argmax(p_ensemble, axis=1)

    # Benchmark metrics
    acc = accuracy_score(y_test, y_pred_ensemble)
    rec_high = recall_score(y_test, y_pred_ensemble, labels=[2], average="micro")
    f1_macro = f1_score(y_test, y_pred_ensemble, average="macro")
    cm = confusion_matrix(y_test, y_pred_ensemble).tolist()

    print("\n--- EVALUATION BENCHMARKS ---")
    print(f"Overall Accuracy:       {acc * 100:.2f}% (Target: >= 85%)")
    print(f"High-Risk Class Recall: {rec_high * 100:.2f}% (Target: >= 90%)")
    print(f"Macro F1-Score:         {f1_macro:.3f} (Target: >= 0.85)")
    print("\nConfusion Matrix [Low, Med, High]:")
    for row in cm:
        print(f"  {row}")

    # Feature Importance from Random Forest
    importances = {
        name: round(float(imp), 4)
        for name, imp in zip(FEATURE_NAMES, rf_model.feature_importances_)
    }
    sorted_importances = dict(sorted(importances.items(), key=lambda item: item[1], reverse=True))
    print("\nFeature Importance Ranking:")
    for f_name, imp in sorted_importances.items():
        print(f"  - {f_name:16}: {imp:.4f}")

    # Save artifacts
    rf_path = os.path.join(MODEL_DIR, "rf_spoilage_model.joblib")
    mlp_path = os.path.join(MODEL_DIR, "nn_spoilage_model.joblib")
    scaler_path = os.path.join(MODEL_DIR, "scaler.joblib")
    meta_path = os.path.join(MODEL_DIR, "model_metadata.json")

    joblib.dump(rf_model, rf_path)
    joblib.dump(mlp_model, mlp_path)
    joblib.dump(scaler, scaler_path)

    metadata = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "n_training_samples": len(X_train),
        "n_test_samples": len(X_test),
        "overall_accuracy": round(float(acc), 4),
        "high_risk_recall": round(float(rec_high), 4),
        "macro_f1": round(float(f1_macro), 4),
        "confusion_matrix": cm,
        "feature_importances": sorted_importances,
        "weights": {"random_forest": 0.55, "neural_network": 0.45},
        "target_met": rec_high >= 0.90 and acc >= 0.85,
    }

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nArtifacts saved successfully in: {MODEL_DIR}")
    return metadata


if __name__ == "__main__":
    train_and_evaluate_models()
