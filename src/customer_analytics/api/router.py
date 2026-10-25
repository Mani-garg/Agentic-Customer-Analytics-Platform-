"""API router aggregating version 1 feature modules."""

from fastapi import APIRouter

from customer_analytics.api.v1.agent import router as agent_router
from customer_analytics.api.v1.analytics import router as analytics_router
from customer_analytics.api.v1.churn import router as churn_router
from customer_analytics.api.v1.segmentation import router as segmentation_router
from customer_analytics.api.v1.simulation import router as simulation_router

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(analytics_router)
v1_router.include_router(segmentation_router)
v1_router.include_router(churn_router)
v1_router.include_router(agent_router)
v1_router.include_router(simulation_router)
