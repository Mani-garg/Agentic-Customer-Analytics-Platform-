"""FastAPI dependency injection providers."""

from functools import lru_cache

from fastapi import Depends

from customer_analytics.agent.factory import AnalyticsAgentService
from customer_analytics.application.agent_service import AgentService
from customer_analytics.application.analytics_service import AnalyticsService
from customer_analytics.application.churn_service import ChurnService
from customer_analytics.application.segmentation_service import SegmentationService
from customer_analytics.application.simulation_service import SimulationService
from customer_analytics.config import Settings, get_settings
from customer_analytics.data.database import DatabaseSessionManager, get_db_manager
from customer_analytics.data.repository import AnalyticsRepository
from customer_analytics.ml.predict import ChurnInferenceService
from customer_analytics.simulation.engine import SimulationEngine


def get_app_settings() -> Settings:
    """Retrieve application settings."""
    return get_settings()


def get_database_manager() -> DatabaseSessionManager:
    """Retrieve database session manager."""
    return get_db_manager()


def get_repository(
    db: DatabaseSessionManager = Depends(get_database_manager),
) -> AnalyticsRepository:
    """Retrieve analytical data repository."""
    return AnalyticsRepository(db_manager=db)


def get_analytics_service(
    repo: AnalyticsRepository = Depends(get_repository),
) -> AnalyticsService:
    """Retrieve general analytics service."""
    return AnalyticsService(repository=repo)


def get_segmentation_service(
    repo: AnalyticsRepository = Depends(get_repository),
) -> SegmentationService:
    """Retrieve customer segmentation service."""
    return SegmentationService(repository=repo)


@lru_cache()
def get_churn_inference_service() -> ChurnInferenceService:
    """Retrieve cached churn inference service."""
    settings = get_settings()
    return ChurnInferenceService(artifact_dir=str(settings.model_artifact_dir))


def get_churn_service(
    inference: ChurnInferenceService = Depends(get_churn_inference_service),
    repo: AnalyticsRepository = Depends(get_repository),
) -> ChurnService:
    """Retrieve churn application service."""
    return ChurnService(inference_service=inference, repository=repo)


def get_simulation_service(
    repo: AnalyticsRepository = Depends(get_repository),
) -> SimulationService:
    """Retrieve simulation application service."""
    engine = SimulationEngine()
    return SimulationService(engine=engine, repository=repo)


def get_agent_service(
    repo: AnalyticsRepository = Depends(get_repository),
) -> AgentService:
    """Retrieve natural-language agent service."""
    agent = AnalyticsAgentService(repository=repo)
    return AgentService(agent=agent)
