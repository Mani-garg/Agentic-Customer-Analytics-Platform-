"""Domain-specific exception hierarchy for the Customer Analytics Platform."""

from typing import Any, Dict, Optional


class PlatformException(Exception):
    """Base exception for all domain and operational errors in the platform."""

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_PLATFORM_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class ConfigurationException(PlatformException):
    """Raised when application configuration is invalid or missing required variables."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="INVALID_CONFIGURATION", details=details)


class DataValidationException(PlatformException):
    """Raised when input datasets fail data quality or schema constraints."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="DATA_VALIDATION_FAILURE", details=details)


class MissingArtifactException(PlatformException):
    """Raised when an expected model or pipeline artifact cannot be found."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="MISSING_ARTIFACT", details=details)


class IncompatibleModelVersionException(PlatformException):
    """Raised when loading an artifact whose schema or version is incompatible."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="INCOMPATIBLE_MODEL_VERSION", details=details)


class DatabaseConnectionException(PlatformException):
    """Raised when connection to the relational persistence layer fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="DATABASE_CONNECTION_ERROR", details=details)


class DatabaseQueryTimeoutException(PlatformException):
    """Raised when a database query exceeds the configured execution timeout."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="DATABASE_QUERY_TIMEOUT", details=details)


class InvalidQuestionException(PlatformException):
    """Raised when a user question cannot be parsed or mapped to supported analytics."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="INVALID_QUESTION", details=details)


class UnsafeSQLException(PlatformException):
    """Raised when an agent-generated SQL query violates security guardrails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="UNSAFE_SQL_VIOLATION", details=details)


class LLMProviderException(PlatformException):
    """Raised when the LLM provider fails, times out, or returns an error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="LLM_PROVIDER_ERROR", details=details)


class AgentExecutionException(PlatformException):
    """Raised when agent execution or tool invocation fails or hits iteration limits."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="AGENT_EXECUTION_FAILURE", details=details)


class ModelInferenceException(PlatformException):
    """Raised when feature inputs fail validation during churn inference."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="MODEL_INFERENCE_ERROR", details=details)


class InvalidSimulationInputException(PlatformException):
    """Raised when revenue recovery simulation inputs violate domain constraints."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="INVALID_SIMULATION_INPUT", details=details)


class MissingRequiredFeatureException(PlatformException):
    """Raised when an inference or feature table is missing mandatory columns."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="MISSING_REQUIRED_FEATURE", details=details)


class UnsupportedSchemaOperationException(PlatformException):
    """Raised when attempting an operation on an unsupported schema or table."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="UNSUPPORTED_SCHEMA_OPERATION", details=details)
