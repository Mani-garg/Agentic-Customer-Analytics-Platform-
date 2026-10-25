"""Probability calibration assessment for churn prediction models."""

from typing import Dict, List

import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss


def assess_calibration(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 5,
) -> Dict[str, object]:
    """Compute Brier score loss and calibration reliability curve bins."""
    brier = float(brier_score_loss(y_true, y_prob))

    # Fractional true positives and mean predicted probabilities
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins, strategy="uniform")

    curve_points: List[Dict[str, float]] = [
        {"mean_predicted_probability": round(float(p), 4), "fraction_positives": round(float(t), 4)}
        for p, t in zip(prob_pred, prob_true, strict=False)
    ]

    return {
        "brier_score": round(brier, 4),
        "calibration_curve": curve_points,
        "interpretation": "Lower Brier score indicates better calibrated probabilities (0.0 is perfect).",
    }
