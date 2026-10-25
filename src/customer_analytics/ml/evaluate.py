"""Comprehensive model evaluation reporting for binary churn classification."""

from typing import Any, Dict

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from customer_analytics.ml.calibration import assess_calibration


def evaluate_classifier(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    operating_threshold: float = 0.50,
) -> Dict[str, Any]:
    """Compute complete suite of classification and ranking metrics given true labels, probabilities, and threshold."""
    y_pred = (y_prob >= operating_threshold).astype(int)

    # Confusion matrix elements
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    # Threshold-dependent metrics
    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    balanced_acc = float(balanced_accuracy_score(y_true, y_pred))

    # Ranking (threshold-independent) metrics
    # Handle single class edge cases gracefully
    if len(np.unique(y_true)) > 1:
        roc_auc = float(roc_auc_score(y_true, y_prob))
        pr_auc = float(average_precision_score(y_true, y_prob))
    else:
        roc_auc = 0.50
        pr_auc = float(np.mean(y_true))

    calibration = assess_calibration(y_true, y_prob)

    report = {
        "operating_threshold": round(operating_threshold, 3),
        "total_evaluated": int(len(y_true)),
        "actual_positives": int(y_true.sum()),
        "actual_negatives": int(len(y_true) - y_true.sum()),
        "confusion_matrix": {
            "true_positives": int(tp),
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
        },
        "metrics": {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "balanced_accuracy": round(balanced_acc, 4),
            "roc_auc": round(roc_auc, 4),
            "pr_auc": round(pr_auc, 4),
            "brier_score": calibration["brier_score"],
        },
        "calibration": calibration,
    }

    return report
