"""FastAPI Application Entrypoint for Customer Analytics Platform."""

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from customer_analytics.api.errors import setup_exception_handlers
from customer_analytics.api.router import v1_router
from customer_analytics.api.v1.health import router as health_router
from customer_analytics.config import get_settings
from customer_analytics.data.database import get_db_manager
from customer_analytics.logging_config import setup_logging
from customer_analytics.observability.request_context import (
    clear_correlation_id,
    set_correlation_id,
)

logger = logging.getLogger("customer_analytics")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup validation and graceful shutdown."""
    settings = get_settings()
    setup_logging(log_level=settings.log_level, json_format=settings.log_json)
    logger.info(
        f"Starting Customer Analytics Platform in [{settings.app_env.upper()}] environment..."
    )

    # Ensure database tables exist
    db = get_db_manager()
    db.create_all_tables()
    logger.info("Relational persistence schema verified and ready.")

    yield

    logger.info("Shutting down Customer Analytics Platform...")


def create_app() -> FastAPI:
    """FastAPI application factory."""
    settings = get_settings()

    app = FastAPI(
        title="Agentic Customer Analytics Platform",
        description=(
            "Production analytics platform combining RFM customer segmentation, "
            "leakage-safe XGBoost churn prediction, guarded natural language querying, "
            "and deterministic what-if revenue recovery simulation."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Middleware: Request Correlation ID & Latency Logging
    @app.middleware("http")
    async def correlation_id_middleware(request: Request, call_next):
        start_time = time.perf_counter()
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        set_correlation_id(correlation_id)

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Response-Time-MS"] = str(duration_ms)

        logger.info(
            f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms} ms)"
        )

        clear_correlation_id()
        return response

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Setup Custom Exception Handlers
    setup_exception_handlers(app)

    # Register Routers
    app.include_router(health_router)
    app.include_router(v1_router)

    return app


app = create_app()


def run_cli():
    """CLI runner command for production entrypoint."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "customer_analytics.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.app_env == "development",
    )


if __name__ == "__main__":
    run_cli()
