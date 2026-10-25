"""Machine learning training pipeline with baselines, class-weighting, and threshold tuning."""

import logging
from pathlib import Path
from typing import Any, Dict, Tuple, Union

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from customer_analytics.data.schemas import MODEL_FEATURE_NAMES
from customer_analytics.exceptions import DataValidationException
from customer_analytics.ml.artifacts import save_model_artifacts
from customer_analytics.ml.evaluate import evaluate_classifier
from customer_analytics.ml.metadata import ModelTrainingMetadata
from customer_analytics.ml.threshold import select_operating_threshold

logger = logging.getLogger(__name__)


def train_churn_model(
    feature_df: pd.DataFrame,
    artifact_dir: Union[str, Path] = "./artifacts/models",
    seed: int = 42,
    model_version: str = "v1.0.0",
    min_precision: float = 0.35,
) -> Tuple[xgb.XGBClassifier, ModelTrainingMetadata, Dict[str, Any]]:
    """Execute complete churn model training, baseline benchmarking, threshold tuning, and artifact persistence."""
    if feature_df.empty:
        raise DataValidationException("Feature DataFrame is empty; cannot train model.")

    if "churn_label" not in feature_df.columns:
        raise DataValidationException("Feature DataFrame lacks mandatory 'churn_label' column.")

    # Drop any rows where churn_label is missing
    clean_features = feature_df.dropna(subset=["churn_label"]).copy()
    clean_features["churn_label"] = clean_features["churn_label"].astype(int)

    # Validate feature presence
    missing_feats = [f for f in MODEL_FEATURE_NAMES if f not in clean_features.columns]
    if missing_feats:
        raise DataValidationException(f"Missing required model features: {missing_feats}")

    X = clean_features[MODEL_FEATURE_NAMES].fillna(0.0).values
    y = clean_features["churn_label"].values

    total_samples = len(y)
    positive_samples = int(y.sum())
    negative_samples = total_samples - positive_samples

    if positive_samples == 0 or negative_samples == 0:
        raise DataValidationException(
            f"Dataset must contain both positive and negative examples. Positives: {positive_samples}, Negatives: {negative_samples}"
        )

    logger.info(
        f"Training dataset: {total_samples} samples, {positive_samples} positives "
        f"({positive_samples / total_samples * 100:.1f}% churn rate)"
    )

    # 1. Stratified train/val/test split: 70% train, 15% val, 15% test
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=0.15, random_state=seed, stratify=y
    )
    val_ratio_of_remaining = 0.15 / 0.85
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val,
        y_train_val,
        test_size=val_ratio_of_remaining,
        random_state=seed,
        stratify=y_train_val,
    )

    train_pos = int(y_train.sum())
    train_neg = int(len(y_train) - train_pos)

    # Class weighting strictly calculated from train set
    scale_pos_weight = float(train_neg / max(1, train_pos))
    logger.info(f"Class imbalance on train set: scale_pos_weight = {scale_pos_weight:.2f}")

    # 2. Fit Baselines on identical train set
    # Baseline A: Majority class baseline
    dummy_baseline = DummyClassifier(strategy="most_frequent")
    dummy_baseline.fit(X_train, y_train)
    (
        dummy_baseline.predict_proba(X_val)[:, 1]
        if len(dummy_baseline.classes_) > 1
        else np.zeros(len(X_val))
    )
    dummy_test_prob = (
        dummy_baseline.predict_proba(X_test)[:, 1]
        if len(dummy_baseline.classes_) > 1
        else np.zeros(len(X_test))
    )
    baseline_eval = evaluate_classifier(y_test, dummy_test_prob, operating_threshold=0.5)

    # Baseline B: Logistic Regression baseline (with standard scaling)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    logreg = LogisticRegression(class_weight="balanced", random_state=seed, max_iter=500)
    logreg.fit(X_train_scaled, y_train)
    logreg_test_prob = logreg.predict_proba(X_test_scaled)[:, 1]
    logreg_eval = evaluate_classifier(y_test, logreg_test_prob, operating_threshold=0.5)

    # 3. Fit XGBoost Classifier
    xgb_params = {
        "n_estimators": 100,
        "max_depth": 4,
        "learning_rate": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "scale_pos_weight": scale_pos_weight,
        "random_state": seed,
        "eval_metric": "logloss",
        "n_jobs": 1,
    }

    model = xgb.XGBClassifier(**xgb_params)
    model.fit(
        X_train,
        y_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )

    # 4. Tune decision threshold on validation set
    y_val_prob = model.predict_proba(X_val)[:, 1]
    best_threshold, val_thresh_metrics, threshold_grid = select_operating_threshold(
        y_true=y_val,
        y_prob=y_val_prob,
        min_precision=min_precision,
    )

    logger.info(
        f"Validation threshold selected: {best_threshold:.3f} "
        f"(Recall: {val_thresh_metrics.get('recall')}, Precision: {val_thresh_metrics.get('precision')})"
    )

    # 5. Evaluate final model on untouched test partition
    y_test_prob = model.predict_proba(X_test)[:, 1]
    test_eval = evaluate_classifier(y_test, y_test_prob, operating_threshold=best_threshold)

    logger.info(
        f"Test set evaluation at threshold {best_threshold:.3f}: "
        f"Recall={test_eval['metrics']['recall']}, Precision={test_eval['metrics']['precision']}, "
        f"PR-AUC={test_eval['metrics']['pr_auc']}, ROC-AUC={test_eval['metrics']['roc_auc']}"
    )

    # 6. Build metadata object
    metadata = ModelTrainingMetadata(
        model_name="XGBoostChurnClassifier",
        model_version=model_version,
        feature_names=list(MODEL_FEATURE_NAMES),
        operating_threshold=best_threshold,
        seed=seed,
        train_size=len(y_train),
        val_size=len(y_val),
        test_size=len(y_test),
        train_positive_count=train_pos,
        train_negative_count=train_neg,
        scale_pos_weight=round(scale_pos_weight, 4),
        hyperparameters=xgb_params,
        metrics=test_eval["metrics"],
    )

    full_evaluation_report = {
        "model_version": model_version,
        "operating_threshold": best_threshold,
        "xgb_test_metrics": test_eval,
        "baseline_dummy_metrics": baseline_eval,
        "baseline_logreg_metrics": logreg_eval,
        "validation_threshold_tuning": {
            "selected_threshold": best_threshold,
            "selected_metrics": val_thresh_metrics,
            "candidate_evaluations_sample": threshold_grid[::10],  # sample 10 points
        },
    }

    # 7. Persist artifacts
    save_model_artifacts(
        model=model,
        metadata=metadata,
        artifact_dir=artifact_dir,
        evaluation_report=full_evaluation_report,
    )

    return model, metadata, full_evaluation_report
