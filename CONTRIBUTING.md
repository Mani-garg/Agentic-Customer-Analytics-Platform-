# Contributing Guidelines

Thank you for your interest in contributing to the **Agentic Customer Analytics Platform**.

## Code of Conduct & Principles

1. **Production Quality**: All submissions must include tests, type annotations, explicit error handling, and documentation updates.
2. **Security First**: Never commit private keys, real customer personal identifiable information (PII), or unsecured query endpoints.
3. **Temporal Integrity**: Do not introduce feature leakage into machine learning pipelines. Features must use only data available prior to the observation cutoff.
4. **Deterministic Foundations**: Ensure core analytics, RFM scoring, and simulation formulas remain pure, deterministic, and independently testable without LLM dependencies.

## Development Workflow

1. Fork or branch from `master` / `main`.
2. Install development dependencies:
   ```bash
   pip install -e ".[dev,spark,llm]"
   ```
3. Run linting and static analysis:
   ```bash
   ruff check .
   ruff format --check .
   mypy src
   ```
4. Run the automated test suite:
   ```bash
   pytest tests/unit tests/integration tests/security -v
   ```
5. Submit a detailed Pull Request describing the changes, tests executed, and evidence of verified functionality.
