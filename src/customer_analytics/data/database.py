"""SQLAlchemy database models and connection management for persistence."""

import logging

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    text,
)
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from customer_analytics.config import get_settings

logger = logging.getLogger(__name__)

Base = declarative_base()
metadata = MetaData()

# Define relational analytics tables

rfm_segments_table = Table(
    "rfm_segments",
    Base.metadata,
    Column("customer_id", String(50), primary_key=True),
    Column("recency_days", Integer, nullable=False),
    Column("frequency", Integer, nullable=False),
    Column("monetary_value", Float, nullable=False),
    Column("r_score", Integer, nullable=False),
    Column("f_score", Integer, nullable=False),
    Column("m_score", Integer, nullable=False),
    Column("rfm_score_str", String(10), nullable=False),
    Column("segment", String(50), nullable=False),
)

customer_features_table = Table(
    "customer_features",
    Base.metadata,
    Column("customer_id", String(50), primary_key=True),
    Column("observation_date", Date, nullable=False),
    Column("recency_days", Integer, nullable=False),
    Column("frequency", Integer, nullable=False),
    Column("monetary_value", Float, nullable=False),
    Column("average_order_value", Float, nullable=False),
    Column("customer_tenure_days", Integer, nullable=False),
    Column("days_since_first_purchase", Integer, nullable=False),
    Column("purchase_gap_mean", Float, nullable=False),
    Column("purchase_gap_std", Float, nullable=False),
    Column("historical_order_count", Integer, nullable=False),
    Column("historical_revenue", Float, nullable=False),
    Column("segment", String(50), nullable=True),
    Column("churn_label", Integer, nullable=True),
)

churn_risk_scores_table = Table(
    "churn_risk_scores",
    Base.metadata,
    Column("customer_id", String(50), primary_key=True),
    Column("churn_probability", Float, nullable=False),
    Column("is_churn_predicted", Integer, nullable=False),
    Column("risk_tier", String(20), nullable=False),
    Column("operating_threshold", Float, nullable=False),
    Column("model_version", String(20), nullable=False),
    Column("scored_at", DateTime, nullable=False),
)

segment_summaries_table = Table(
    "segment_summaries",
    Base.metadata,
    Column("segment", String(50), primary_key=True),
    Column("customer_count", Integer, nullable=False),
    Column("customer_percentage", Float, nullable=False),
    Column("total_revenue", Float, nullable=False),
    Column("average_revenue_per_customer", Float, nullable=False),
    Column("average_order_frequency", Float, nullable=False),
    Column("average_recency_days", Float, nullable=False),
    Column("retention_priority", String(100), nullable=False),
)

daily_metrics_table = Table(
    "daily_metrics",
    Base.metadata,
    Column("metric_date", Date, primary_key=True),
    Column("gross_revenue", Float, nullable=False),
    Column("order_count", Integer, nullable=False),
    Column("active_customers", Integer, nullable=False),
    Column("average_order_value", Float, nullable=False),
)


class DatabaseSessionManager:
    """Manages SQLAlchemy engines and session pools for application and read-only agent roles."""

    def __init__(self, db_url: str = None, agent_db_url: str = None):
        settings = get_settings()
        self.db_url = db_url or settings.database_url
        self.agent_db_url = agent_db_url or settings.agent_database_url or self.db_url

        # Check SQLite or PostgreSQL
        connect_args = {}
        if "sqlite" in self.db_url:
            connect_args = {"check_same_thread": False}

        self.app_engine = create_engine(
            self.db_url,
            echo=False,
            pool_pre_ping=True,
            connect_args=connect_args,
        )

        agent_connect_args = dict(connect_args)
        if "sqlite" in self.agent_db_url:
            # For SQLite read-only agent access, query_only pragma can be set
            pass

        self.agent_engine = create_engine(
            self.agent_db_url,
            echo=False,
            pool_pre_ping=True,
            connect_args=agent_connect_args,
        )

        self.AppSessionFactory = sessionmaker(bind=self.app_engine, autoflush=False)
        self.AgentSessionFactory = sessionmaker(bind=self.agent_engine, autoflush=False)

    def create_all_tables(self) -> None:
        """Create tables in the application database."""
        Base.metadata.create_all(self.app_engine)

    def get_app_session(self) -> Session:
        """Return a session for standard application read/write operations."""
        return self.AppSessionFactory()

    def get_agent_session(self) -> Session:
        """Return a session for agent queries with read-only intent."""
        session = self.AgentSessionFactory()
        if "sqlite" in self.agent_db_url:
            session.execute(text("PRAGMA query_only = ON;"))
        return session


# Global singleton instance
_db_manager = None


def get_db_manager() -> DatabaseSessionManager:
    """Get or create singleton DatabaseSessionManager."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseSessionManager()
        _db_manager.create_all_tables()
    return _db_manager
