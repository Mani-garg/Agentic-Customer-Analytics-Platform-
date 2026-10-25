# Development and Engineering Standards

## 1. Local Environment Setup

### 1.1 Prerequisites
- **Python**: `>= 3.11` (Tested on Python 3.11, 3.12, 3.13)
- **Git**
- *(Optional)* Java 8, 11, or 17 if testing PySpark locally.
- *(Optional)* Docker and Docker Compose if testing containerized execution.

### 1.2 Installation
```bash
# Clone and enter directory
cd customer_analytics_platform

# Install dependencies in editable mode
pip install -e ".[dev,spark,llm]"
```

---

## 2. Developer Workflow Commands

### Running Data & ML Pipelines
```bash
# Generate synthetic dataset
python scripts/generate_sample_data.py --output data/raw/transactions.csv --n-customers 1000 --seed 42

# Validate data quality
python scripts/validate_data.py --input data/raw/transactions.csv --report artifacts/reports/data_quality_report.json

# Execute analytical pipeline
python scripts/run_pipeline.py --input data/raw/transactions.csv --output data/processed/customer_features.parquet

# Train churn model and tune threshold
python scripts/train_model.py --features data/processed/customer_features.parquet --artifact-dir artifacts/models

# Run full end-to-end demo
python scripts/demo.py
```

### Running the API Server
```bash
uvicorn customer_analytics.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 3. Testing & Code Quality Assurance

### Run Automated Tests
```bash
# Run entire test suite (unit, integration, security)
pytest tests/unit tests/integration tests/security -v

# Run security tests only
pytest tests/security -v
```

### Code Formatting and Linting
```bash
# Run Ruff linting
ruff check .

# Run Ruff formatting check
ruff format --check .

# Type check with mypy
mypy src
```

---

## 4. Engineering Conventions

- **Zero Temporal Leakage**: Predictive features must strictly use data on or before observation cutoff $T$. Never compute features using transactions occurring in the target prediction horizon.
- **Pure Financial Domain Functions**: Simulation formulas must remain pure, deterministic, and independently tested.
- **Least-Privilege SQL**: Queries must never use unrestricted application roles or bypass AST parsing.
