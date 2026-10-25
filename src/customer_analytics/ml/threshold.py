"""Decision threshold optimization prioritizing recall for customer churn retention."""

from typing import Dict, List, Tuple

import numpy as np
from sklearn.metrics import f1_score, precision_recall_curve, precision_score, recall_score


def select_operating_threshold(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    min_precision: float = 0.35,
    beta: float = 2.0,
) -> Tuple[float, Dict[str, float], List[Dict[str, float]]]:
    """Select optimal decision threshold on validation set prioritizing recall under a minimum precision constraint.

    If no threshold satisfies min_precision, select the threshold maximizing F-beta (with beta > 1 favoring recall).
    """
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_prob)

    comparison_records: List[Dict[str, float]] = []
    candidate_thresholds = np.linspace(0.10, 0.90, 41)

    best_threshold = 0.50
    best_recall = -1.0
    best_metrics = {}

    # Also track best F-beta in case min_precision cannot be met
    best_fbeta = -1.0
    fallback_threshold = 0.50
    fallback_metrics = {}

    beta_sq = beta**2

    for thresh in candidate_thresholds:
        y_pred = (y_prob >= thresh).astype(int)

        rec = float(recall_score(y_true, y_pred, zero_division=0))
        prec = float(precision_score(y_true, y_pred, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, zero_division=0))

        # F-beta calculation: (1 + beta^2) * (P * R) / (beta^2 * P + R)
        if (beta_sq * prec + rec) > 0:
            fbeta = float((1 + beta_sq) * (prec * rec) / (beta_sq * prec + rec))
        else:
            fbeta = 0.0

        record = {
            "threshold": round(float(thresh), 3),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "f_beta": round(fbeta, 4),
            "positive_predictions": int(y_pred.sum()),
        }
        comparison_records.append(record)

        # Track fallback based on F-beta
        if fbeta > best_fbeta:
            best_fbeta = fbeta
            fallback_threshold = float(thresh)
            fallback_metrics = record

        # Primary selection: satisfy min_precision and maximize recall
        if prec >= min_precision:
            if rec > best_recall:
                best_recall = rec
                best_threshold = float(thresh)
                best_metrics = record

    # If constraint was satisfied, use best_threshold; otherwise use F-beta fallback
    if best_metrics:
        chosen_threshold = best_threshold
        chosen_metrics = best_metrics
    else:
        chosen_threshold = fallback_threshold
        chosen_metrics = fallback_metrics

    return chosen_threshold, chosen_metrics, comparison_records
