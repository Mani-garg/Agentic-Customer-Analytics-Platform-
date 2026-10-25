"""Customer segmentation endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from customer_analytics.api.dependencies import get_segmentation_service
from customer_analytics.application.segmentation_service import SegmentationService
from customer_analytics.domain.models import SegmentSummary

router = APIRouter(prefix="/segments", tags=["Segmentation"])


@router.get(
    "",
    response_model=List[SegmentSummary],
    summary="List Customer Segments",
    description="Retrieve aggregated analytical profiles across all customer segments.",
)
def list_segments(
    service: SegmentationService = Depends(get_segmentation_service),
) -> List[SegmentSummary]:
    return service.list_segments()


@router.get(
    "/{segment_name}",
    response_model=SegmentSummary,
    summary="Get Single Segment",
    description="Retrieve the profile of a specific segment (e.g., 'Champions', 'At Risk').",
)
def get_segment(
    segment_name: str,
    service: SegmentationService = Depends(get_segmentation_service),
) -> SegmentSummary:
    segment = service.get_segment(segment_name)
    if not segment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer segment '{segment_name}' not found.",
        )
    return segment
