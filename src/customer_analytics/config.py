"""Central validated configuration management for Customer Analytics Platform."""

from pathlib import Path
from typing import List, Optional, Set

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from customer_analytics.exceptions import ConfigurationException


class Settings(BaseSettings):
    """Application settings with strict validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application Environment
    app_env: str = Field(
        default="development", description="Runtime environment: development, testing, production"
    )
    api_host: str = Field(default="0.0.0.0", description="API bind host")
    api_port: int = Field(default=8000, ge=1024, le=65535, description="API bind port")
    log_level: str = Field(
        default="INFO", description="Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
    log_json: bool = Field(default=False, description="Whether to emit structured JSON logs")

    # Persistence
    database_url: str = Field(
        default="sqlite:///./data/analytics.db",
        description="Primary database connection string for application read/write access",
    )
    agent_database_url: Optional[str] = Field(
        default="sqlite:///./data/analytics.db",
        description="Dedicated least-privilege read-only connection string for agent queries",
    )

    # Spark Engine
    spark_enabled: bool = Field(
        default=False, description="Enable PySpark for large scale batch processing"
    )
    spark_master: str = Field(default="local[*]", description="Spark master connection string")
    spark_app_name: str = Field(
        default="CustomerAnalyticsPlatform", description="Spark application name"
    )

    # File and Directory Paths
    data_dir: Path = Field(default=Path("./data"), description="Base data directory")
    raw_data_path: Path = Field(
        default=Path("./data/raw/transactions.csv"), description="Path to raw transaction CSV"
    )
    processed_data_path: Path = Field(
        default=Path("./data/processed/customer_features.parquet"),
        description="Path to processed customer features Parquet",
    )
    model_artifact_dir: Path = Field(
        default=Path("./artifacts/models"), description="Directory storing model binaries"
    )
    report_dir: Path = Field(
        default=Path("./artifacts/reports"),
        description="Directory storing data quality and evaluation reports",
    )

    # Analytics & ML Parameters
    reproducibility_seed: int = Field(
        default=42, description="Random seed for data generation and training splits"
    )
    model_version: str = Field(
        default="v1.0.0", description="Model version tag for lineage tracking"
    )
    churn_observation_days: int = Field(
        default=180, ge=30, description="Length of historical observation window in days"
    )
    churn_horizon_days: int = Field(
        default=90, ge=14, description="Length of future target prediction horizon in days"
    )
    recall_minimum_precision: float = Field(
        default=0.35,
        ge=0.0,
        le=1.0,
        description="Minimum acceptable precision constraint during threshold tuning",
    )

    # SQL Security & Guardrails
    sql_max_query_length: int = Field(
        default=1000, ge=50, le=10000, description="Maximum character length of agent SQL queries"
    )
    sql_statement_timeout_ms: int = Field(
        default=5000, ge=500, le=60000, description="Database statement timeout in milliseconds"
    )
    sql_max_rows: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Hard limit on number of rows returned by agent queries",
    )
    sql_allowed_tables: Set[str] = Field(
        default={
            "rfm_segments",
            "customer_features",
            "daily_metrics",
            "segment_summaries",
            "churn_risk_scores",
            "cohort_retention",
        },
        description="Allow-list of tables and views accessible to agent queries",
    )

    # Natural Language Agent (Optional)
    llm_provider: Optional[str] = Field(
        default="none", description="LLM provider: 'none', 'mock', 'openai', 'anthropic'"
    )
    llm_model: Optional[str] = Field(default=None, description="LLM model identifier")
    llm_api_key: Optional[str] = Field(default=None, description="Optional LLM API key")
    agent_timeout_seconds: float = Field(
        default=30.0, ge=1.0, le=120.0, description="Agent execution timeout in seconds"
    )

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origin origins",
    )

    @field_validator("app_env")
    @classmethod
    def validate_app_env(cls, v: str) -> str:
        valid_envs = {"development", "testing", "production"}
        v_lower = v.lower()
        if v_lower not in valid_envs:
            raise ConfigurationException(
                f"Invalid APP_ENV '{v}'. Must be one of {valid_envs}",
                details={"provided": v, "allowed": list(valid_envs)},
            )
        return v_lower

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ConfigurationException(
                f"Invalid LOG_LEVEL '{v}'. Must be one of {valid_levels}",
                details={"provided": v, "allowed": list(valid_levels)},
            )
        return v_upper

    @field_validator("sql_allowed_tables", mode="before")
    @classmethod
    def parse_allowed_tables(cls, v: object) -> Set[str]:
        if isinstance(v, str):
            return {t.strip().lower() for t in v.split(",") if t.strip()}
        if isinstance(v, (list, set, tuple)):
            return {str(t).strip().lower() for t in v if str(t).strip()}
        return set()

    def ensure_directories(self) -> None:
        """Create necessary directories if they do not exist."""
        for path in [
            self.data_dir,
            self.data_dir / "raw",
            self.data_dir / "processed",
            self.data_dir / "sample",
            self.model_artifact_dir,
            self.report_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)


# Global settings singleton
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Retrieve or initialize application settings."""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.ensure_directories()
    return _settings


def reset_settings() -> None:
    """Reset the settings singleton (useful for testing)."""
    global _settings
    _settings = None
