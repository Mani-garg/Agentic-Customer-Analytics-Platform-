# Changelog

All notable changes to the **Agentic Customer Analytics Platform** will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-26

### Added
- **Data Ingestion & Validation Pipeline**:
  - Full CSV transaction reader with explicit Pydantic schema validation.
  - Comprehensive data quality validation suite (null IDs, negative quantities/prices, date plausibility, currency checks).
  - Machine-readable structured `DataQualityReport` with rejected records categorization.
  - Realistic synthetic transaction generator with temporal churn simulation.
- **Scalable Customer Analytics & RFM Engine**:
  - Pluggable Analytics Engine supporting PySpark batch processing with seamless local in-memory fallback.
  - Pure deterministic RFM metric calculation with configurable quantile scoring and tie-breaking.
  - 8-tier interpretable customer segmentation (Champions, Loyal Customers, Potential Loyalists, New Customers, At Risk, Hibernating, About to Sleep, Promising).
  - Cohort retention matrix computation.
- **Machine Learning Churn Prediction**:
  - Leakage-safe customer feature engineering on temporal observation window.
  - Logistic Regression and Majority Class baselines.
  - XGBoost binary classifier with positive class weight adjustment for target imbalance.
  - Validation set threshold tuning with recall prioritization.
  - Comprehensive evaluation reporting (Precision, Recall, F1, PR-AUC, ROC-AUC, Brier score, Confusion Matrix).
  - Model serialization, metadata tracking, and reproducible inference service.
- **Guarded Agentic Analytics Interface**:
  - Multi-tier SQL Guard with AST query parsing (`sqlglot`).
  - Strict table allow-listing and rejection of multi-statement, DDL, DML, CTE writes, and catalog access.
  - 10 strongly-typed analytics tools with strict input schemas.
  - LangChain ReAct agent orchestration with graceful deterministic rule-based query fallback when no LLM key is configured.
- **Deterministic Revenue-Recovery Simulator**:
  - Multi-scenario discount simulation engine evaluating redemption, retention, and campaign economics.
  - Net incremental value estimation with boundary condition checks and assumption disclaimers.
  - 2D sensitivity matrix generator for scenario comparison.
- **FastAPI REST API**:
  - Versioned API (`/api/v1`) with endpoints for health, analytics overview, segmentation, churn prediction, agent query, and simulation.
  - Standardized error handling, request correlation IDs, and structured logging.
- **Production DevOps & Testing**:
  - Automated test suite covering unit, integration, and security/adversarial injection tests.
  - Multi-stage Dockerfile and Docker Compose configuration.
  - GitHub Actions CI workflow for linting, type-checking, and test automation.
