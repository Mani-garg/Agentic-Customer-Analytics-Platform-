"""Application service orchestrating retention discount simulations."""

from typing import Any, Dict, List

from customer_analytics.data.repository import AnalyticsRepository
from customer_analytics.domain.models import SimulationResult, SimulationScenario
from customer_analytics.simulation.engine import SimulationEngine
from customer_analytics.simulation.schemas import DiscountSimulationRequest
from customer_analytics.simulation.sensitivity import run_sensitivity_grid


class SimulationService:
    """Orchestrates what-if financial simulations and multi-scenario comparisons."""

    def __init__(self, engine: SimulationEngine, repository: AnalyticsRepository):
        self.engine = engine
        self.repo = repository

    def _resolve_target_population(self, target_pop: str) -> int:
        """Determine eligible customer count based on target selection."""
        overview = self.repo.get_overview_metrics()
        target_lower = target_pop.lower().strip()

        if "high_risk" in target_lower:
            count = overview.get("high_risk_customers", 0)
            return count if count > 0 else 100
        if "at_risk" in target_lower:
            summaries = self.repo.get_segment_summaries()
            for s in summaries:
                if s.segment.value.lower() == "at risk":
                    return s.customer_count
            return 150
        return overview.get("total_customers", 500)

    def run_discount_simulation(self, req: DiscountSimulationRequest) -> SimulationResult:
        """Execute a single retention discount simulation."""
        overview = self.repo.get_overview_metrics()
        eligible_count = self._resolve_target_population(req.target_population)
        arpu = req.expected_future_revenue_per_retained or overview.get(
            "avg_revenue_per_customer", 125.0
        )

        scenario = SimulationScenario(
            scenario_id="sim_custom",
            name=req.scenario_name,
            target_population=req.target_population,
            discount_percentage=req.discount_percentage,
            max_discount_per_customer=req.max_discount_per_customer,
            expected_redemption_rate=req.expected_redemption_rate,
            estimated_retention_probability=req.estimated_retention_probability,
            expected_future_revenue_per_retained=arpu,
            campaign_cost_per_contacted=req.campaign_cost_per_contacted,
            max_customers_to_contact=req.max_customers_to_contact,
        )

        return self.engine.simulate_scenario(
            scenario, customer_count=eligible_count, avg_monetary=arpu
        )

    def compare_scenarios(
        self, requests: List[DiscountSimulationRequest]
    ) -> List[SimulationResult]:
        """Compare multiple scenarios on equal customer footing."""
        overview = self.repo.get_overview_metrics()
        eligible_count = self._resolve_target_population(requests[0].target_population)
        arpu = overview.get("avg_revenue_per_customer", 125.0)

        scenarios = [
            SimulationScenario(
                scenario_id=f"sim_{i + 1}",
                name=r.scenario_name,
                target_population=r.target_population,
                discount_percentage=r.discount_percentage,
                max_discount_per_customer=r.max_discount_per_customer,
                expected_redemption_rate=r.expected_redemption_rate,
                estimated_retention_probability=r.estimated_retention_probability,
                expected_future_revenue_per_retained=r.expected_future_revenue_per_retained or arpu,
                campaign_cost_per_contacted=r.campaign_cost_per_contacted,
                max_customers_to_contact=r.max_customers_to_contact,
            )
            for i, r in enumerate(requests)
        ]

        return self.engine.compare_scenarios(
            scenarios, customer_count=eligible_count, avg_monetary=arpu
        )

    def run_sensitivity(
        self,
        base_req: DiscountSimulationRequest,
        discount_rates: List[float],
        redemption_rates: List[float],
    ) -> Dict[str, Any]:
        """Compute parameter sensitivity matrix."""
        overview = self.repo.get_overview_metrics()
        eligible_count = self._resolve_target_population(base_req.target_population)
        arpu = base_req.expected_future_revenue_per_retained or overview.get(
            "avg_revenue_per_customer", 125.0
        )

        scenario = SimulationScenario(
            scenario_id="base_sens",
            name=base_req.scenario_name,
            target_population=base_req.target_population,
            discount_percentage=base_req.discount_percentage,
            max_discount_per_customer=base_req.max_discount_per_customer,
            expected_redemption_rate=base_req.expected_redemption_rate,
            estimated_retention_probability=base_req.estimated_retention_probability,
            expected_future_revenue_per_retained=arpu,
            campaign_cost_per_contacted=base_req.campaign_cost_per_contacted,
            max_customers_to_contact=base_req.max_customers_to_contact,
        )

        return run_sensitivity_grid(
            base_scenario=scenario,
            eligible_population=eligible_count,
            baseline_arpu=arpu,
            discount_rates=discount_rates,
            redemption_rates=redemption_rates,
        )
