"""Application service for general customer and revenue analytics."""

from typing import Any, Dict

from customer_analytics.data.repository import AnalyticsRepository


class AnalyticsService:
    """Orchestrates customer analytics queries and metric definitions."""

    def __init__(self, repository: AnalyticsRepository):
        self.repo = repository

    def get_overview(self) -> Dict[str, Any]:
        """Retrieve high-level active analytical metrics."""
        return self.repo.get_overview_metrics()
