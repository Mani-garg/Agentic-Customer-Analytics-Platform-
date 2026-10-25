"""Application service for customer RFM segmentation profiles."""

from typing import List, Optional

from customer_analytics.data.repository import AnalyticsRepository
from customer_analytics.domain.models import SegmentSummary


class SegmentationService:
    """Orchestrates segment retrieval and customer filtering."""

    def __init__(self, repository: AnalyticsRepository):
        self.repo = repository

    def list_segments(self) -> List[SegmentSummary]:
        """Retrieve all active segment profiles."""
        return self.repo.get_segment_summaries()

    def get_segment(self, segment_name: str) -> Optional[SegmentSummary]:
        """Retrieve profile for a specific segment name."""
        summaries = self.list_segments()
        target = segment_name.strip().lower()
        for s in summaries:
            if s.segment.value.lower() == target:
                return s
        return None
