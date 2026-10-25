"""Shared pytest fixtures and test configuration."""

import tempfile
from datetime import date
from pathlib import Path
from typing import Generator

import pandas as pd
import pytest
from starlette.testclient import TestClient

from customer_analytics.data.database import DatabaseSessionManager
from customer_analytics.data.repository import AnalyticsRepository
from customer_analytics.data.synthetic import generate_synthetic_transactions
from customer_analytics.features.build_features import build_customer_feature_table
from customer_analytics.main import create_app


@pytest.fixture(scope="session")
def sample_transactions_df() -> pd.DataFrame:
    """Generate a consistent, small transactional dataset for testing."""
    return generate_synthetic_transactions(n_customers=100, seed=42)


@pytest.fixture(scope="session")
def sample_features_df(sample_transactions_df: pd.DataFrame) -> pd.DataFrame:
    """Generate customer feature vectors with churn labels at cutoff."""
    cutoff = date(2026, 6, 30)
    return build_customer_feature_table(
        transactions_df=sample_transactions_df,
        observation_cutoff=cutoff,
        churn_horizon_days=90,
    )


@pytest.fixture
def temp_db_manager() -> Generator[DatabaseSessionManager, None, None]:
    """Provide a temporary SQLite database session manager for isolated tests."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = f.name

    db_url = f"sqlite:///{temp_path}"
    manager = DatabaseSessionManager(db_url=db_url, agent_db_url=db_url)
    manager.create_all_tables()

    yield manager

    # Teardown
    manager.app_engine.dispose()
    manager.agent_engine.dispose()
    try:
        Path(temp_path).unlink(missing_ok=True)
    except Exception:
        pass


@pytest.fixture
def populated_repository(
    temp_db_manager: DatabaseSessionManager,
    sample_features_df: pd.DataFrame,
) -> AnalyticsRepository:
    """Provide an AnalyticsRepository populated with test data."""
    repo = AnalyticsRepository(db_manager=temp_db_manager)
    repo.sync_feature_dataframe_to_db(sample_features_df)
    return repo


@pytest.fixture
def test_client(populated_repository: AnalyticsRepository) -> Generator[TestClient, None, None]:
    """FastAPI TestClient with injected test repository."""
    from customer_analytics.api.dependencies import get_repository

    app = create_app()
    app.dependency_overrides[get_repository] = lambda: populated_repository

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
