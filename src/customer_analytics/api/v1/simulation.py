"""Retention discount simulation and what-if financial modeling endpoints."""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from customer_analytics.api.dependencies import get_simulation_service
from customer_analytics.application.simulation_service import SimulationService
from customer_analytics.domain.models import SimulationResult
from customer_analytics.simulation.schemas import (
    DiscountSimulationRequest,
    MultiScenarioComparisonRequest,
    SensitivityAnalysisRequest,
)

router = APIRouter(prefix="/simulations", tags=["Simulation"])


@router.post(
    "/discount",
    response_model=SimulationResult,
    summary="Simulate Discount Scenario",
    description="Run a deterministic what-if revenue recovery simulation for a retention discount strategy.",
)
def simulate_discount(
    req: DiscountSimulationRequest,
    service: SimulationService = Depends(get_simulation_service),
) -> SimulationResult:
    return service.run_discount_simulation(req)


@router.post(
    "/compare",
    response_model=List[SimulationResult],
    summary="Compare Retention Scenarios",
    description="Evaluate and rank multiple alternative discount strategies on identical baseline populations.",
)
def compare_scenarios(
    req: MultiScenarioComparisonRequest,
    service: SimulationService = Depends(get_simulation_service),
) -> List[SimulationResult]:
    return service.compare_scenarios(req.scenarios)


@router.post(
    "/sensitivity",
    summary="Run Parameter Sensitivity Grid",
    description="Compute a 2D sensitivity matrix evaluating net incremental value across varying discount and redemption rates.",
)
def run_sensitivity(
    req: SensitivityAnalysisRequest,
    service: SimulationService = Depends(get_simulation_service),
) -> Dict[str, Any]:
    return service.run_sensitivity(
        base_req=req.base_scenario,
        discount_rates=req.discount_rates,
        redemption_rates=req.redemption_rates,
    )
