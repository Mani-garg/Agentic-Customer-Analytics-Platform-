"""Global exception handlers for the FastAPI application."""

import logging
from datetime import datetime, timezone

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from customer_analytics.api.v1.schemas import ErrorResponse
from customer_analytics.exceptions import (
    DatabaseConnectionException,
    DatabaseQueryTimeoutException,
    DataValidationException,
    InvalidQuestionException,
    InvalidSimulationInputException,
    MissingArtifactException,
    MissingRequiredFeatureException,
    PlatformException,
    UnsafeSQLException,
)
from customer_analytics.observability.request_context import get_correlation_id

logger = logging.getLogger(__name__)


def setup_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers on the FastAPI app."""

    @app.exception_handler(UnsafeSQLException)
    async def unsafe_sql_handler(request: Request, exc: UnsafeSQLException) -> JSONResponse:
        cid = get_correlation_id()
        logger.warning(f"[{cid}] SQL Guard violation: {exc.message}")
        err = ErrorResponse(
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            correlation_id=cid,
            timestamp=datetime.now(timezone.utc),
        )
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=err.model_dump())

    @app.exception_handler(DataValidationException)
    @app.exception_handler(InvalidSimulationInputException)
    @app.exception_handler(MissingRequiredFeatureException)
    @app.exception_handler(InvalidQuestionException)
    async def validation_exception_handler(
        request: Request, exc: PlatformException
    ) -> JSONResponse:
        cid = get_correlation_id()
        logger.warning(f"[{cid}] Validation failure: {exc.message}")
        err = ErrorResponse(
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            correlation_id=cid,
            timestamp=datetime.now(timezone.utc),
        )
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=err.model_dump())

    @app.exception_handler(MissingArtifactException)
    async def missing_artifact_handler(
        request: Request, exc: MissingArtifactException
    ) -> JSONResponse:
        cid = get_correlation_id()
        logger.error(f"[{cid}] Missing artifact: {exc.message}")
        err = ErrorResponse(
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            correlation_id=cid,
            timestamp=datetime.now(timezone.utc),
        )
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=err.model_dump())

    @app.exception_handler(DatabaseConnectionException)
    @app.exception_handler(DatabaseQueryTimeoutException)
    async def database_error_handler(request: Request, exc: PlatformException) -> JSONResponse:
        cid = get_correlation_id()
        logger.error(f"[{cid}] Database error: {exc.message}")
        err = ErrorResponse(
            error_code=exc.error_code,
            message="Database service temporarily unavailable or timed out.",
            details={},  # Never expose internal database traces
            correlation_id=cid,
            timestamp=datetime.now(timezone.utc),
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=err.model_dump()
        )

    @app.exception_handler(RequestValidationError)
    async def pydantic_validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        cid = get_correlation_id()
        logger.warning(f"[{cid}] Request body validation error: {exc.errors()}")
        err = ErrorResponse(
            error_code="REQUEST_VALIDATION_ERROR",
            message="Invalid request schema or parameters.",
            details={"errors": exc.errors()},
            correlation_id=cid,
            timestamp=datetime.now(timezone.utc),
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=err.model_dump()
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        cid = get_correlation_id()
        logger.exception(f"[{cid}] Unhandled internal exception: {exc}")
        err = ErrorResponse(
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected internal error occurred. Please reference the correlation ID.",
            details={},
            correlation_id=cid,
            timestamp=datetime.now(timezone.utc),
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=err.model_dump()
        )
