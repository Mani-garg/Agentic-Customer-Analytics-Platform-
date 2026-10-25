"""PySpark session lifecycle manager with environment detection and graceful fallback."""

import logging
import os
import shutil
from typing import Any, Optional

logger = logging.getLogger(__name__)


def is_spark_available() -> bool:
    """Check whether PySpark and a valid Java runtime are present on the system."""
    java_bin = shutil.which("java")
    if not java_bin and not os.environ.get("JAVA_HOME"):
        logger.debug("Java runtime not found on PATH or JAVA_HOME; PySpark execution disabled.")
        return False

    try:
        import pyspark  # noqa: F401

        return True
    except ImportError:
        logger.debug("pyspark module not installed; PySpark execution disabled.")
        return False


class SparkSessionManager:
    """Manages creation, reuse, and teardown of PySpark session."""

    _session: Optional[Any] = None

    @classmethod
    def get_or_create_session(
        cls,
        app_name: str = "CustomerAnalyticsPlatform",
        master: str = "local[*]",
    ) -> Optional[Any]:
        """Obtain active SparkSession if PySpark and Java are present; returns None otherwise."""
        if cls._session is not None:
            return cls._session

        if not is_spark_available():
            logger.info(
                "Using lightweight in-memory analytics engine (PySpark/Java not configured)."
            )
            return None

        try:
            from pyspark.sql import SparkSession

            logger.info(f"Initializing PySpark session '{app_name}' on master '{master}'...")
            session = (
                SparkSession.builder.appName(app_name)
                .master(master)
                .config("spark.driver.memory", "2g")
                .config("spark.sql.shuffle.partitions", "4")
                .config("spark.ui.enabled", "false")
                .getOrCreate()
            )
            cls._session = session
            return cls._session
        except Exception as e:
            logger.warning(
                f"Failed to initialize PySpark session: {e}. Falling back to in-memory engine."
            )
            return None

    @classmethod
    def stop_session(cls) -> None:
        """Safely stop and clear the active SparkSession."""
        if cls._session is not None:
            try:
                cls._session.stop()
            except Exception as e:
                logger.error(f"Error stopping Spark session: {e}")
            finally:
                cls._session = None
