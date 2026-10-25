"""Two-dimensional parameter sensitivity analysis for retention scenarios."""

from typing import Any, Dict, List

from customer_analytics.domain.models import SimulationScenario
from customer_analytics.simulation.economics import compute_scenario_economics


def run_sensitivity_grid(
    base_scenario: SimulationScenario,
    eligible_population: int,
    baseline_arpu: float,
    discount_rates: List[float],
    redemption_rates: List[float],
) -> Dict[str, Any]:
    """Generate a bounded 2D sensitivity grid evaluating net incremental value across discount and redemption rates."""
    grid_results: List[Dict[str, Any]] = []

    for d_rate in discount_rates:
        row_cells = []
        for r_rate in redemption_rates:
            modified_scenario = SimulationScenario(
                scenario_id=f"{base_scenario.scenario_id}_d{int(d_rate * 100)}_r{int(r_rate * 100)}",
                name=f"{base_scenario.name} (D:{int(d_rate * 100)}%, R:{int(r_rate * 100)}%)",
                target_population=base_scenario.target_population,
                discount_percentage=d_rate,
                max_discount_per_customer=base_scenario.max_discount_per_customer,
                expected_redemption_rate=r_rate,
                estimated_retention_probability=base_scenario.estimated_retention_probability,
                expected_future_revenue_per_retained=base_scenario.expected_future_revenue_per_retained,
                campaign_cost_per_contacted=base_scenario.campaign_cost_per_contacted,
                max_customers_to_contact=base_scenario.max_customers_to_contact,
            )

            result = compute_scenario_economics(
                scenario=modified_scenario,
                eligible_population_size=eligible_population,
                baseline_arpu=baseline_arpu,
            )

            row_cells.append(
                {
                    "discount_rate": d_rate,
                    "redemption_rate": r_rate,
                    "net_incremental_value": result.estimated_net_incremental_value,
                    "total_cost": result.total_cost,
                    "retained_customers": result.expected_retained_customers,
                    "roi_percentage": result.roi_percentage,
                }
            )
        grid_results.extend(row_cells)

    # Determine best scenario under assumptions
    best_cell = max(grid_results, key=lambda c: c["net_incremental_value"])

    return {
        "base_scenario_name": base_scenario.name,
        "eligible_population": eligible_population,
        "grid_evaluations": grid_results,
        "optimal_point_under_assumptions": {
            "discount_rate": best_cell["discount_rate"],
            "redemption_rate": best_cell["redemption_rate"],
            "max_net_incremental_value": best_cell["net_incremental_value"],
        },
        "disclaimer": "Optimal parameter combination is conditional entirely on specified model assumptions.",
    }
