"""Health and readiness probe endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response
from sqlalchemy import text

from customer_analytics.api.dependencies import get_app_settings, get_database_manager
from customer_analytics.api.v1.schemas import HealthResponse
from customer_analytics.config import Settings
from customer_analytics.data.database import DatabaseSessionManager

router = APIRouter(tags=["Health"])


@router.get("/health/live", response_model=HealthResponse, summary="Liveness Probe")
def liveness(settings: Settings = Depends(get_app_settings)) -> HealthResponse:
    """Return process liveness confirmation."""
    return HealthResponse(
        status="live",
        timestamp=datetime.now(timezone.utc),
        app_env=settings.app_env,
        version="1.0.0",
        details={"process": "healthy"},
    )


@router.get("/health/ready", response_model=HealthResponse, summary="Readiness Probe")
def readiness(
    response: Response,
    settings: Settings = Depends(get_app_settings),
    db: DatabaseSessionManager = Depends(get_database_manager),
) -> HealthResponse:
    """Verify application dependency readiness without performing heavy model training or table scans."""
    details = {}
    is_ready = True

    # 1. Database check
    try:
        with db.get_app_session() as session:
            session.execute(text("SELECT 1"))
        details["database"] = "ready"
    except Exception:
        details["database"] = "degraded"
        details["database_note"] = "Database connection test failed."

    # 2. Model artifact directory check
    if settings.model_artifact_dir.exists():
        details["model_storage"] = "ready"
    else:
        details["model_storage"] = "missing_directory"

    details["spark"] = (
        "enabled" if settings.spark_enabled else "disabled (lightweight engine active)"
    )
    details["llm_provider"] = settings.llm_provider or "none"

    return HealthResponse(
        status="ready" if is_ready else "degraded",
        timestamp=datetime.now(timezone.utc),
        app_env=settings.app_env,
        version="1.0.0",
        details=details,
    )
