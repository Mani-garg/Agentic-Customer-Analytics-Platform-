.PHONY: help install generate-data validate-data pipeline train evaluate run-api test test-unit test-integration test-security lint type-check docker-build docker-up docker-down demo clean

help:
	@echo "Available commands:"
	@echo "  make install           - Install project dependencies"
	@echo "  make generate-data     - Generate synthetic e-commerce transactions"
	@echo "  make validate-data     - Validate raw dataset against data quality rules"
	@echo "  make pipeline          - Execute data ingestion, RFM aggregation, and feature tables"
	@echo "  make train             - Train churn prediction models with threshold tuning"
	@echo "  make evaluate          - Evaluate saved model on test partition"
	@echo "  make run-api           - Launch FastAPI application server"
	@echo "  make test              - Run all automated tests (unit, integration, security)"
	@echo "  make test-unit         - Run unit tests only"
	@echo "  make test-integration  - Run integration tests only"
	@echo "  make test-security     - Run SQL injection and boundary security tests"
	@echo "  make lint              - Check code formatting and style with ruff"
	@echo "  make type-check        - Run static type checks with mypy"
	@echo "  make docker-build      - Build Docker container image"
	@echo "  make docker-up         - Start services with Docker Compose"
	@echo "  make docker-down       - Stop Docker Compose services"
	@echo "  make demo              - Run end-to-end demo workflow script"
	@echo "  make clean             - Clean transient build and cache files"

install:
	pip install -e ".[dev,spark,llm]"

generate-data:
	python scripts/generate_sample_data.py --output data/raw/transactions.csv --n-customers 1000 --seed 42

validate-data:
	python scripts/validate_data.py --input data/raw/transactions.csv --report artifacts/reports/data_quality_report.json

pipeline:
	python scripts/run_pipeline.py --input data/raw/transactions.csv --output data/processed/customer_features.parquet

train:
	python scripts/train_model.py --features data/processed/customer_features.parquet --artifact-dir artifacts/models

evaluate:
	python scripts/evaluate_model.py --artifact-dir artifacts/models --report-dir artifacts/reports

run-api:
	uvicorn customer_analytics.main:app --host 0.0.0.0 --port 8000 --reload

test:
	pytest tests/unit tests/integration tests/security -v

test-unit:
	pytest tests/unit -v

test-integration:
	pytest tests/integration -v

test-security:
	pytest tests/security -v

lint:
	ruff check src tests scripts
	ruff format --check src tests scripts

type-check:
	mypy src

docker-build:
	docker build -t customer-analytics-platform:latest .

docker-up:
	docker compose up -d

docker-down:
	docker compose down

demo:
	python scripts/demo.py

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .ruff_cache .mypy_cache __pycache__
