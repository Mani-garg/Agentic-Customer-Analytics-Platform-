"""Churn prediction and risk prioritization endpoints."""

from typing import List

from fastapi import APIRouter, Depends, Query

from customer_analytics.api.dependencies import get_churn_service
from customer_analytics.api.v1.schemas import (
    ChurnPredictionRequest,
    ChurnPredictionResponse,
    ChurnSummaryResponse,
    HighRiskCustomerResponse,
)
from customer_analytics.application.churn_service import ChurnService
from customer_analytics.domain.models import CustomerFeatureRecord

router = APIRouter(prefix="/churn", tags=["Churn Prediction"])


@router.get(
    "/summary",
    response_model=ChurnSummaryResponse,
    summary="Get Churn Model Summary",
    description="Retrieve model metadata, operating threshold, and overall churn risk distribution.",
)
def get_summary(
    service: ChurnService = Depends(get_churn_service),
) -> ChurnSummaryResponse:
    data = service.get_summary()
    return ChurnSummaryResponse(**data)


@router.post(
    "/predict",
    response_model=ChurnPredictionResponse,
    summary="Predict Customer Churn",
    description="Score churn probability and risk tier for a customer feature record.",
)
def predict_churn(
    req: ChurnPredictionRequest,
    service: ChurnService = Depends(get_churn_service),
) -> ChurnPredictionResponse:
    features = CustomerFeatureRecord(**req.model_dump())
    result = service.predict_churn(features)
    return ChurnPredictionResponse(
        customer_id=result.customer_id,
        churn_probability=result.churn_probability,
        is_churn_predicted=result.is_churn_predicted,
        risk_tier=result.risk_tier,
        operating_threshold=result.operating_threshold,
        model_version=result.model_version,
        explanation=result.explanation,
        timestamp=result.timestamp,
    )


@router.get(
    "/high-risk",
    response_model=List[HighRiskCustomerResponse],
    summary="Get High Risk Customers",
    description="Retrieve a paginated list of high-risk customers for retention campaign targeting.",
)
def get_high_risk_customers(
    limit: int = Query(default=20, ge=1, le=100, description="Page limit"),
    offset: int = Query(default=0, ge=0, description="Page offset"),
    service: ChurnService = Depends(get_churn_service),
) -> List[HighRiskCustomerResponse]:
    rows = service.get_high_risk_customers(limit=limit, offset=offset)
    return [HighRiskCustomerResponse(**r) for r in rows]
