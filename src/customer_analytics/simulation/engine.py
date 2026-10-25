"""Revenue-recovery simulation engine implementing the domain simulation contract."""

import logging
from typing import List

from customer_analytics.domain.contracts import SimulationEngineInterface
from customer_analytics.domain.models import SimulationResult, SimulationScenario
from customer_analytics.simulation.economics import compute_scenario_economics

logger = logging.getLogger(__name__)


class SimulationEngine(SimulationEngineInterface):
    """Deterministic business simulation engine."""

    def simulate_scenario(
        self,
        scenario: SimulationScenario,
        customer_count: int,
        avg_monetary: float,
    ) -> SimulationResult:
        """Execute single discount simulation scenario."""
        logger.info(
            f"Executing simulation for scenario '{scenario.name}' on {customer_count} eligible customers."
        )
        return compute_scenario_economics(
            scenario=scenario,
            eligible_population_size=customer_count,
            baseline_arpu=avg_monetary,
        )

    def compare_scenarios(
        self,
        scenarios: List[SimulationScenario],
        customer_count: int,
        avg_monetary: float,
    ) -> List[SimulationResult]:
        """Compare multiple scenarios on equal financial footing."""
        results: List[SimulationResult] = []
        for sc in scenarios:
            res = self.simulate_scenario(
                sc, customer_count=customer_count, avg_monetary=avg_monetary
            )
            results.append(res)

        # Sort by estimated net incremental value descending
        results.sort(key=lambda r: r.estimated_net_incremental_value, reverse=True)
        return results
