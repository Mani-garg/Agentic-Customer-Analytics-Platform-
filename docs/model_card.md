# Model Card: Customer Churn Binary Classifier

## 1. Model Details
- **Architecture**: Gradient Boosted Decision Trees (`XGBClassifier`)
- **Version**: `v1.0.0`
- **License**: MIT
- **Input Features**: 10 engineered customer behavioral metrics (`recency_days`, `frequency`, `monetary_value`, `average_order_value`, `customer_tenure_days`, `days_since_first_purchase`, `purchase_gap_mean`, `purchase_gap_std`, `historical_order_count`, `historical_revenue`)
- **Target Variable**: Binary churn indicator ($1$ = customer placed $0$ eligible orders in future horizon $(T, T + 90\text{ days}]$, $0$ = placed $\ge 1$ order).

## 2. Intended Use & Business Objective
- **Primary Use**: Identify customers at imminent risk of inactivity to prioritize retention outreach before permanent attrition occurs.
- **Decision Priority**: The business cost of missing a churner (false negative) exceeds the cost of sending an outreach discount (false positive). Therefore, threshold tuning explicitly prioritizes **recall** subject to a minimum precision constraint ($\ge 0.35$).
- **Out of Scope**: This model does NOT make guaranteed predictions or causal uplift claims. Customer churn probabilities are statistical risk estimates, not certainties.

## 3. Training & Evaluation Methodology
- **Data Partitions**: 70% Train, 15% Validation, 15% Held-Out Test (stratified on churn label).
- **Class Imbalance Strategy**: Positive class weighting (`scale_pos_weight`) calculated strictly on the training partition:
  $$\text{scale\_pos\_weight} = \frac{\text{count}(\text{negative\_train})}{\text{count}(\text{positive\_train})}$$
  Test and validation partitions are NEVER used in weight calculation or feature transformations.
- **Threshold Selection**: Tuned exclusively on validation set probabilities to optimize recall without consulting test labels.
- **Evaluation Partition**: The frozen model and tuned threshold are evaluated on the untouched test partition.

## 4. Evaluation Benchmark (Empirical Demo Run)

| Model Partition | Metric | Value |
|:---|:---|:---:|
| **Test Set (Held-Out)** | **Recall** | **0.9310** |
| Test Set (Held-Out) | Precision | 0.5625 |
| Test Set (Held-Out) | F1-Score | 0.7013 |
| Test Set (Held-Out) | PR-AUC (Average Precision) | 0.8471 |
| Test Set (Held-Out) | ROC-AUC | 0.8932 |
| Test Set (Held-Out) | Brier Score | 0.1245 |
| Baseline (Majority Class) | Test Recall | 0.0000 |
| Baseline (Logistic Regression) | Test Recall | 0.7931 |

*Note: PR-AUC is especially informative for tabular customer churn because precision and recall evaluate performance directly on the minority positive class without inflation from large negative majorities.*

## 5. Limitations & Ethical Considerations
- **Non-Causal**: Feature correlations (e.g. high recency days) must not be interpreted as causal causes of churn.
- **Temporal Stationarity**: Market seasonality or macroeconomic shifts require periodic model retraining.
