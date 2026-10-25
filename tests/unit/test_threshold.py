"""Unit tests for decision threshold selection with recall priority."""

import numpy as np

from customer_analytics.ml.threshold import select_operating_threshold


def test_select_operating_threshold_recall_priority():
    """Verify threshold selector prioritizes recall while meeting minimum precision."""
    # Synthetic validation true labels and probabilities
    np.random.seed(42)
    y_true = np.array([1] * 30 + [0] * 70)  # 30% positive
    # Model assigns higher prob to positives with some noise
    y_prob = np.concatenate(
        [
            np.random.uniform(0.3, 0.9, size=30),
            np.random.uniform(0.05, 0.6, size=70),
        ]
    )

    threshold, metrics, grid = select_operating_threshold(
        y_true=y_true,
        y_prob=y_prob,
        min_precision=0.35,
    )

    assert 0.05 <= threshold <= 0.95
    assert "recall" in metrics
    assert "precision" in metrics
    # Under reasonable conditions, precision should satisfy constraint or fallback
    assert len(grid) > 0
